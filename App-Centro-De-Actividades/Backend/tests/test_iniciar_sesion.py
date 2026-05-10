import unittest

from src.core.bcrypt_and_session import bcrypt
from src.core.database import db
from src.core.models.persona import (
    Empleado,
    Permiso,
    Persona,
    PersonaRolPuente,
    Rol,
    RolPermisoPuente,
    Socio,
)
from src.web import create_app


class IniciarSesionTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_login_como_empleado_autentica_y_crea_sesion(self):
        self._crear_persona(
            email="empleado@example.com",
            password="1234",
            como_empleado=True,
            roles={"empleado": ["usuarios:ver", "clases:ver"]},
        )

        response = self.client.post(
            "/api/login",
            json={"email": "empleado@example.com", "password": "1234"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "authenticated")
        self.assertEqual(response.json["session"]["role"], "empleado")
        self.assertEqual(
            response.json["session"]["permissions"],
            ["clases:ver", "usuarios:ver"],
        )

    def test_login_como_administrador_es_directo_y_exclusivo(self):
        self._crear_persona(
            email="admin@example.com",
            password="1234",
            roles={"administrador": ["usuarios:gestionar", "metricas:ver"]},
        )

        response = self.client.post(
            "/api/login",
            json={"email": "admin@example.com", "password": "1234"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "authenticated")
        self.assertEqual(response.json["session"]["role"], "administrador")

    def test_login_con_dos_roles_pide_seleccion_y_luego_autentica(self):
        self._crear_persona(
            email="mixto@example.com",
            password="1234",
            como_empleado=True,
            como_socio=True,
            roles={
                "empleado": ["usuarios:ver", "clases:ver"],
                "socio": ["reservas:crear", "pagos:ver_propios"],
            },
        )

        login_response = self.client.post(
            "/api/login",
            json={"email": "mixto@example.com", "password": "1234"},
        )

        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(login_response.json["status"], "role_selection_required")
        self.assertEqual(set(login_response.json["available_roles"]), {"empleado", "socio"})

        select_response = self.client.post(
            "/api/login/select-role",
            json={"role": "socio"},
        )

        self.assertEqual(select_response.status_code, 200)
        self.assertEqual(select_response.json["status"], "authenticated")
        self.assertEqual(select_response.json["session"]["role"], "socio")
        self.assertEqual(
            select_response.json["session"]["permissions"],
            ["pagos:ver_propios", "reservas:crear"],
        )

    def test_login_falla_si_email_no_existe(self):
        response = self.client.post(
            "/api/login",
            json={"email": "desconocido@example.com", "password": "1234"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json["message"],
            "El email no se encuentra registrado en el sistema.",
        )

    def test_login_falla_si_password_es_incorrecta(self):
        self._crear_persona(
            email="empleado@example.com",
            password="1234",
            como_socio=True,
            roles={"socio": ["reservas:crear"]},
        )

        response = self.client.post(
            "/api/login",
            json={"email": "empleado@example.com", "password": "9999"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json["message"], "La contraseña es incorrecta.")

    def test_obtener_estado_sesion_devuelve_pendiente_de_seleccion(self):
        self._crear_persona(
            email="mixto@example.com",
            password="1234",
            como_empleado=True,
            como_socio=True,
            roles={
                "empleado": ["usuarios:ver"],
                "socio": ["pagos:ver_propios"],
            },
        )

        self.client.post(
            "/api/login",
            json={"email": "mixto@example.com", "password": "1234"},
        )

        response = self.client.get("/api/login/session")

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json["authenticated"])
        self.assertTrue(response.json["pending_role_selection"])

    def test_autorizacion_backend_confirma_permiso_del_rol_activo(self):
        self._crear_persona(
            email="admin@example.com",
            password="1234",
            roles={"administrador": ["usuarios:gestionar", "metricas:ver"]},
        )

        self.client.post(
            "/api/login",
            json={"email": "admin@example.com", "password": "1234"},
        )

        allowed_response = self.client.post(
            "/api/login/authorize",
            json={"permission": "usuarios:gestionar"},
        )
        denied_response = self.client.post(
            "/api/login/authorize",
            json={"permission": "pagos:ver_propios"},
        )

        self.assertEqual(allowed_response.status_code, 200)
        self.assertTrue(allowed_response.json["authorized"])
        self.assertEqual(denied_response.status_code, 200)
        self.assertFalse(denied_response.json["authorized"])

    def _crear_persona(
        self,
        email,
        password,
        como_empleado=False,
        como_socio=False,
        roles=None,
    ):
        persona = Persona(
            email=email,
            password_hash=bcrypt.generate_password_hash(password).decode("utf-8"),
            nombre="Ada",
            apellido="Lovelace",
            estado="activo",
        )
        db.session.add(persona)
        db.session.flush()

        if como_empleado:
            db.session.add(Empleado(persona_id=persona.persona_id))
        if como_socio:
            db.session.add(Socio(persona_id=persona.persona_id))

        for role_name, permissions in (roles or {}).items():
            role = self._obtener_o_crear_rol(role_name, permissions)
            db.session.add(
                PersonaRolPuente(persona_id=persona.persona_id, rol_id=role.rol_id)
            )

        db.session.commit()
        return persona

    def _obtener_o_crear_rol(self, role_name, permissions):
        role = Rol.query.filter_by(nombre=role_name).first()
        if role is None:
            role = Rol(nombre=role_name, descripcion=f"Rol {role_name}")
            db.session.add(role)
            db.session.flush()

        existing_codes = {permiso.codigo for permiso in role.permisos}
        for permission_code in permissions:
            permiso = Permiso.query.filter_by(codigo=permission_code).first()
            if permiso is None:
                permiso = Permiso(
                    codigo=permission_code,
                    descripcion=f"Permiso {permission_code}",
                )
                db.session.add(permiso)
                db.session.flush()

            if permission_code not in existing_codes:
                db.session.add(
                    RolPermisoPuente(rol_id=role.rol_id, permiso_id=permiso.permiso_id)
                )
                existing_codes.add(permission_code)

        return role
