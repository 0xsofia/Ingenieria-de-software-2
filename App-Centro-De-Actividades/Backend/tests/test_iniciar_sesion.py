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
from src.core.seeds.usuarios import DEFAULT_PASSWORD, seed_usuarios
from src.web import create_app

UNKNOWN_EMAIL = "example123@gmail.com"


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

    def test_login_como_empleado_requiere_seleccion_y_autentica(self):
        self._crear_persona(
            email="empleado@centro.test",
            password=DEFAULT_PASSWORD,
            como_empleado=True,
            como_socio=True,
            roles={
                "empleado": ["usuarios:ver", "clases:ver"],
                "socio": ["reservas:crear", "pagos:ver_propios"],
            },
        )

        login_response = self.client.post(
            "/api/login",
            json={"email": "empleado@centro.test", "password": DEFAULT_PASSWORD},
        )

        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(login_response.json["status"], "role_selection_required")
        self.assertEqual(
            set(login_response.json["available_roles"]), {"empleado", "socio"}
        )

        select_response = self.client.post(
            "/api/login/select-role",
            json={"role": "empleado"},
        )

        self.assertEqual(select_response.status_code, 200)
        self.assertEqual(select_response.json["status"], "authenticated")
        self.assertEqual(select_response.json["session"]["role"], "empleado")
        self.assertEqual(
            select_response.json["session"]["permissions"],
            ["clases:ver", "usuarios:ver"],
        )

    def test_login_como_socio_con_credenciales_de_empleado_autentica(self):
        self._crear_persona(
            email="empleado@centro.test",
            password=DEFAULT_PASSWORD,
            como_empleado=True,
            como_socio=True,
            roles={
                "empleado": ["usuarios:ver", "clases:ver"],
                "socio": ["reservas:crear", "pagos:ver_propios"],
            },
        )

        login_response = self.client.post(
            "/api/login",
            json={"email": "empleado@centro.test", "password": DEFAULT_PASSWORD},
        )

        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(login_response.json["status"], "role_selection_required")

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

    def test_login_como_socio_sin_credenciales_de_empleado_autentica(self):
        self._crear_persona(
            email="socio@centro.test",
            password=DEFAULT_PASSWORD,
            como_socio=True,
            roles={"socio": ["reservas:crear"]},
        )

        response = self.client.post(
            "/api/login",
            json={"email": "socio@centro.test", "password": DEFAULT_PASSWORD},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "authenticated")
        self.assertEqual(response.json["session"]["role"], "socio")

    def test_login_falla_si_email_no_existe(self):
        response = self.client.post(
            "/api/login",
            json={"email": UNKNOWN_EMAIL, "password": DEFAULT_PASSWORD},
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json["message"],
            "El email no se encuentra registrado en el sistema.",
        )

    def test_login_falla_si_password_es_incorrecta(self):
        self._crear_persona(
            email="socio@centro.test",
            password=DEFAULT_PASSWORD,
            como_socio=True,
            roles={"socio": ["reservas:crear"]},
        )

        response = self.client.post(
            "/api/login",
            json={"email": "socio@centro.test", "password": "1234"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json["message"], "La contraseña es incorrecta.")

    def test_login_como_administrador_es_directo_y_exclusivo(self):
        self._crear_persona(
            email="admin@centro.test",
            password=DEFAULT_PASSWORD,
            roles={"administrador": ["usuarios:gestionar", "metricas:ver"]},
        )

        response = self.client.post(
            "/api/login",
            json={"email": "admin@centro.test", "password": DEFAULT_PASSWORD},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "authenticated")
        self.assertEqual(response.json["session"]["role"], "administrador")

    def test_obtener_estado_sesion_devuelve_pendiente_de_seleccion(self):
        self._crear_persona(
            email="empleado@centro.test",
            password=DEFAULT_PASSWORD,
            como_empleado=True,
            como_socio=True,
            roles={
                "empleado": ["usuarios:ver"],
                "socio": ["pagos:ver_propios"],
            },
        )

        self.client.post(
            "/api/login",
            json={"email": "empleado@centro.test", "password": DEFAULT_PASSWORD},
        )

        response = self.client.get("/api/login/session")

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json["authenticated"])
        self.assertTrue(response.json["pending_role_selection"])

    def test_obtener_estado_sesion_reconstruye_usuario_autenticado(self):
        self._crear_persona(
            email="empleado@example.com",
            password=DEFAULT_PASSWORD,
            como_empleado=True,
            roles={"empleado": ["usuarios:ver", "clases:ver"]},
        )

        self.client.post(
            "/api/login",
            json={"email": "empleado@example.com", "password": DEFAULT_PASSWORD},
        )

        response = self.client.get("/api/login/session")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json["authenticated"])
        self.assertEqual(response.json["session"]["role"], "empleado")
        self.assertEqual(
            response.json["session"]["permissions"],
            ["clases:ver", "usuarios:ver"],
        )

    def test_autorizacion_backend_confirma_permiso_del_rol_activo(self):
        self._crear_persona(
            email="admin@example.com",
            password=DEFAULT_PASSWORD,
            roles={"administrador": ["usuarios:gestionar", "metricas:ver"]},
        )

        self.client.post(
            "/api/login",
            json={"email": "admin@example.com", "password": DEFAULT_PASSWORD},
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

    def test_logout_cierra_sesion_y_desautentica(self):
        self._crear_persona(
            email="admin@example.com",
            password=DEFAULT_PASSWORD,
            roles={"administrador": []},
        )

        self.client.post(
            "/api/login",
            json={"email": "admin@example.com", "password": DEFAULT_PASSWORD},
        )

        logout_response = self.client.post("/api/session/logout")
        session_response = self.client.get("/api/login/session")

        self.assertEqual(logout_response.status_code, 200)
        self.assertEqual(logout_response.json["status"], "logged_out")
        self.assertEqual(logout_response.json["redirect_to"], "/login")
        self.assertEqual(session_response.status_code, 200)
        self.assertFalse(session_response.json["authenticated"])

    def test_seed_usuarios_cubre_los_tres_accesos_basicos_de_la_hu(self):
        seed_usuarios()

        self.assertEqual(Persona.query.count(), 3)

        admin_response = self.client.post(
            "/api/login",
            json={"email": "admin@centro.test", "password": DEFAULT_PASSWORD},
        )
        self.assertEqual(admin_response.status_code, 200)
        self.assertEqual(admin_response.json["session"]["role"], "administrador")

        self.client.post("/api/session/logout")

        empleado_response = self.client.post(
            "/api/login",
            json={"email": "empleado@centro.test", "password": DEFAULT_PASSWORD},
        )
        self.assertEqual(empleado_response.status_code, 200)
        self.assertEqual(empleado_response.json["status"], "role_selection_required")
        self.assertEqual(
            set(empleado_response.json["available_roles"]), {"empleado", "socio"}
        )

        socio_desde_empleado_response = self.client.post(
            "/api/login/select-role",
            json={"role": "socio"},
        )
        self.assertEqual(socio_desde_empleado_response.status_code, 200)
        self.assertEqual(
            socio_desde_empleado_response.json["session"]["role"], "socio"
        )

        self.client.post("/api/session/logout")

        socio_response = self.client.post(
            "/api/login",
            json={"email": "socio@centro.test", "password": DEFAULT_PASSWORD},
        )
        self.assertEqual(socio_response.status_code, 200)
        self.assertEqual(socio_response.json["session"]["role"], "socio")

    def test_cli_seed_db_puebla_usuarios_si_schema_esta_preparado(self):
        runner = self.app.test_cli_runner()

        result = runner.invoke(args=["seed_db"])

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(Persona.query.count(), 3)

        response = self.client.post(
            "/api/login",
            json={"email": "admin@centro.test", "password": DEFAULT_PASSWORD},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["session"]["role"], "administrador")

    def test_cli_seed_db_falla_si_schema_no_esta_preparado(self):
        db.drop_all()
        runner = self.app.test_cli_runner()

        result = runner.invoke(args=["seed_db"])

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Primero ejecuta `flask reset-db`", result.output)

    def _crear_persona(
        self,
        email,
        password,
        como_empleado=False,
        como_socio=False,
        roles=None,
    ):
        persona = Persona(
            dni=f"3000000{Persona.query.count() + 1}",
            email=email,
            password_hash=bcrypt.generate_password_hash(password).decode("utf-8"),
            nombre="Ada",
            apellido="Lovelace",
            telefono=f"01115{Persona.query.count() + 1:08d}",
            calle="Calle Falsa",
            numero_puerta="123",
            codigo_postal="1900",
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
