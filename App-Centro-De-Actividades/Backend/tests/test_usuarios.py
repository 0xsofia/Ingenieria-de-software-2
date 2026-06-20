import unittest
from datetime import date, datetime, time, timezone, timedelta
from decimal import Decimal
from unittest.mock import patch

from src.core.bcrypt_and_session import bcrypt
from src.core.database import db
from src.core.enums.clase_enum import ActividadEnum, NivelEnum, TipoClaseEnum
from src.core.models.clase import Clase
from src.core.models.lista_espera import ListaEspera
from src.core.models.pago import Pago
from src.core.models.persona import Empleado, Persona, PersonaRolPuente, Rol, Socio
from src.core.models.profesor import Profesor
from src.core.models.reserva import Reserva
from src.core.services.mailjet_email import EmailDeliveryError
from src.web import create_app


class UsuariosTestCase(unittest.TestCase):
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

    @patch("src.core.services.registrarse.send_employee_access_email")
    @patch("src.core.services.registrarse.generate_temporary_password")
    def test_admin_puede_registrar_empleado_con_envio_de_password_temporal(
        self, mock_generate_temporary_password, mock_send_employee_access_email
    ):
        mock_generate_temporary_password.return_value = "Temp42#Pwd"
        empleado_role = self._crear_rol("empleado")
        socio_role = self._crear_rol("socio")
        self._crear_usuario_con_roles(
            email="admin@centro.test",
            dni="30000001",
            password="123456",
            roles=["administrador"],
        )
        self._login_admin()

        response = self.client.post("/api/usuarios/empleados", json=self._payload_empleado())

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["status"], "registered")
        self.assertEqual(response.json["redirect_to"], "/usuarios")
        self.assertIn("email", response.json["message"])

        persona = Persona.query.filter_by(email="jorge.petri@example.com").first()
        self.assertIsNotNone(persona)
        self.assertIsNotNone(db.session.get(Empleado, persona.persona_id))
        self.assertIsNotNone(db.session.get(Socio, persona.persona_id))
        self.assertTrue(
            bcrypt.check_password_hash(persona.password_hash, "Temp42#Pwd")
        )
        self.assertIsNotNone(
            PersonaRolPuente.query.filter_by(
                persona_id=persona.persona_id, rol_id=empleado_role.rol_id
            ).first()
        )
        self.assertIsNotNone(
            PersonaRolPuente.query.filter_by(
                persona_id=persona.persona_id, rol_id=socio_role.rol_id
            ).first()
        )
        mock_send_employee_access_email.assert_called_once_with(
            recipient_email="jorge.petri@example.com",
            recipient_name="Jorge",
            temporary_password="Temp42#Pwd",
        )

    @patch("src.core.services.registrarse.send_employee_access_email")
    @patch("src.core.services.registrarse.generate_temporary_password")
    def test_registro_de_empleado_falla_si_no_se_puede_enviar_el_email(
        self, mock_generate_temporary_password, mock_send_employee_access_email
    ):
        mock_generate_temporary_password.return_value = "Temp42#Pwd"
        mock_send_employee_access_email.side_effect = EmailDeliveryError(
            "No se pudo enviar el email con la contraseña temporal del empleado."
        )
        self._crear_rol("empleado")
        self._crear_rol("socio")
        self._crear_usuario_con_roles(
            email="admin@centro.test",
            dni="30000001",
            password="123456",
            roles=["administrador"],
        )
        self._login_admin()

        response = self.client.post("/api/usuarios/empleados", json=self._payload_empleado())

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json["status"], "error")
        self.assertEqual(
            response.json["message"],
            "No se pudo enviar el email con la contraseña temporal del empleado.",
        )
        self.assertIsNone(Persona.query.filter_by(email="jorge.petri@example.com").first())

    def test_registro_de_empleado_falla_si_no_hay_sesion_admin(self):
        self._crear_rol("empleado")

        response = self.client.post("/api/usuarios/empleados", json=self._payload_empleado())

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json["status"], "error")

    def test_registro_de_empleado_falla_si_el_usuario_no_es_admin(self):
        self._crear_rol("empleado")
        self._crear_usuario_con_roles(
            email="socio@centro.test",
            dni="30000003",
            password="123456",
            roles=["socio"],
        )
        self.client.post(
            "/api/login",
            json={"email": "socio@centro.test", "password": "123456"},
        )

        response = self.client.post("/api/usuarios/empleados", json=self._payload_empleado())

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json["status"], "error")

    def test_registro_de_empleado_reutiliza_validacion_de_dni_y_telefono(self):
        self._crear_rol("empleado")
        self._crear_rol("socio")
        self._crear_usuario_con_roles(
            email="admin@centro.test",
            dni="30000001",
            password="123456",
            roles=["administrador"],
        )
        self._crear_persona(dni="33333333", email="existente@centro.test")
        self._login_admin()

        duplicate_response = self.client.post(
            "/api/usuarios/empleados",
            json=self._payload_empleado(dni="33333333"),
        )
        phone_response = self.client.post(
            "/api/usuarios/empleados",
            json=self._payload_empleado(dni="44444444", telefono="221 444-663A"),
        )

        self.assertEqual(duplicate_response.status_code, 400)
        self.assertEqual(
            duplicate_response.json["errors"]["dni"],
            "El DNI ya se encuentra registrado en el sistema.",
        )
        self.assertEqual(phone_response.status_code, 400)
        self.assertEqual(
            phone_response.json["errors"]["telefono"],
            "Ingrese un telefono valido sin caracteres especiales, letras o espacios. Ejemplo 2214446633",
        )

    def test_admin_puede_obtener_usuario_modificable(self):
        self._crear_usuario_con_roles(
            email="admin@centro.test",
            dni="30000001",
            password="123456",
            roles=["administrador"],
        )
        persona = self._crear_usuario_con_roles(
            email="jorge.petri@example.com",
            dni="33333333",
            password="123456",
            roles=["empleado"],
        )
        self._login_admin()

        response = self.client.get(f"/api/usuarios/{persona.persona_id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "ok")
        self.assertEqual(response.json["user"]["dni"], "33333333")
        self.assertEqual(response.json["user"]["roles"], ["empleado"])

    def test_admin_puede_listar_usuarios_modificables(self):
        self._crear_usuario_con_roles(
            email="admin@centro.test",
            dni="30000001",
            password="123456",
            roles=["administrador"],
        )
        self._crear_usuario_con_roles(
            email="empleado@centro.test",
            dni="30000002",
            password="123456",
            roles=["empleado"],
        )
        self._crear_usuario_con_roles(
            email="socio@centro.test",
            dni="30000003",
            password="123456",
            roles=["socio"],
        )
        self._login_admin()

        response = self.client.get("/api/usuarios")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "ok")
        self.assertEqual(len(response.json["users"]), 2)
        self.assertEqual(
            [user["roles"] for user in response.json["users"]],
            [["empleado"], ["socio"]],
        )

    def test_empleado_puede_filtrar_usuarios_por_dni_email_y_nombre(self):
        self._crear_usuario_con_roles(
            email="empleado@centro.test",
            dni="30000002",
            password="123456",
            roles=["empleado"],
        )
        socio = self._crear_usuario_con_roles(
            email="killiam@gmail.com",
            dni="44000000",
            password="123456",
            roles=["socio"],
        )
        socio.nombre = "Killiam"
        socio.apellido = "Mbape"
        db.session.commit()
        self.client.post(
            "/api/login",
            json={"email": "empleado@centro.test", "password": "123456"},
        )

        response_by_dni = self.client.get("/api/usuarios?dni=44000000")
        response_by_email = self.client.get("/api/usuarios?email=KILLIAM@GMAIL.COM")
        response_by_name = self.client.get("/api/usuarios?nombre=killiam mbape")

        self.assertEqual(response_by_dni.status_code, 200)
        self.assertEqual(len(response_by_dni.json["users"]), 1)
        self.assertEqual(response_by_dni.json["users"][0]["dni"], "44000000")

        self.assertEqual(response_by_email.status_code, 200)
        self.assertEqual(len(response_by_email.json["users"]), 1)
        self.assertEqual(response_by_email.json["users"][0]["email"], "killiam@gmail.com")

        self.assertEqual(response_by_name.status_code, 200)
        self.assertEqual(len(response_by_name.json["users"]), 1)
        self.assertEqual(response_by_name.json["users"][0]["email"], "killiam@gmail.com")

    def test_listado_de_usuarios_devuelve_vacio_si_no_hay_coincidencias(self):
        self._crear_usuario_con_roles(
            email="admin@centro.test",
            dni="30000001",
            password="123456",
            roles=["administrador"],
        )
        self._login_admin()

        response = self.client.get("/api/usuarios?nombre=nadie")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["users"], [])

    def test_listado_de_usuarios_falla_si_usuario_no_tiene_permiso(self):
        self._crear_usuario_con_roles(
            email="socio@centro.test",
            dni="30000003",
            password="123456",
            roles=["socio"],
        )
        self.client.post(
            "/api/login",
            json={"email": "socio@centro.test", "password": "123456"},
        )

        response = self.client.get("/api/usuarios")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json["status"], "error")

    def test_admin_puede_modificar_usuario_sin_cambiar_email(self):
        self._crear_usuario_con_roles(
            email="admin@centro.test",
            dni="30000001",
            password="123456",
            roles=["administrador"],
        )
        persona = self._crear_usuario_con_roles(
            email="jorge.petri@example.com",
            dni="33333333",
            password="123456",
            roles=["empleado"],
        )
        self._login_admin()

        response = self.client.put(
            f"/api/usuarios/{persona.persona_id}",
            json=self._payload_empleado(nombre="Luis", apellido="Sosa"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "updated")
        self.assertEqual(response.json["message"], "El usuario ha sido actualizado con éxito.")

        updated_persona = db.session.get(Persona, persona.persona_id)
        self.assertEqual(updated_persona.nombre, "Luis")
        self.assertEqual(updated_persona.apellido, "Sosa")
        self.assertEqual(updated_persona.email, "jorge.petri@example.com")

    def test_admin_puede_modificar_usuario_cambiando_email(self):
        self._crear_usuario_con_roles(
            email="admin@centro.test",
            dni="30000001",
            password="123456",
            roles=["administrador"],
        )
        persona = self._crear_usuario_con_roles(
            email="jorge.petri@example.com",
            dni="33333333",
            password="123456",
            roles=["socio"],
        )
        self._login_admin()

        response = self.client.put(
            f"/api/usuarios/{persona.persona_id}",
            json=self._payload_empleado(email="jorge.petri+ok@example.com"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "updated")
        self.assertEqual(
            db.session.get(Persona, persona.persona_id).email,
            "jorge.petri+ok@example.com",
        )

    def test_modificacion_de_usuario_falla_si_email_ya_existe(self):
        self._crear_usuario_con_roles(
            email="admin@centro.test",
            dni="30000001",
            password="123456",
            roles=["administrador"],
        )
        persona = self._crear_usuario_con_roles(
            email="jorge.petri@example.com",
            dni="33333333",
            password="123456",
            roles=["empleado"],
        )
        self._crear_persona(dni="44444444", email="existente@centro.test")
        self._login_admin()

        response = self.client.put(
            f"/api/usuarios/{persona.persona_id}",
            json=self._payload_empleado(email="existente@centro.test"),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["status"], "validation_error")
        self.assertEqual(
            response.json["errors"]["email"],
            "El email ya se encuentra registrado en el sistema.",
        )

    def test_modificacion_de_usuario_falla_si_intentan_cambiar_dni(self):
        self._crear_usuario_con_roles(
            email="admin@centro.test",
            dni="30000001",
            password="123456",
            roles=["administrador"],
        )
        persona = self._crear_usuario_con_roles(
            email="jorge.petri@example.com",
            dni="33333333",
            password="123456",
            roles=["empleado"],
        )
        self._login_admin()

        response = self.client.put(
            f"/api/usuarios/{persona.persona_id}",
            json=self._payload_empleado(dni="99999999"),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["status"], "validation_error")
        self.assertEqual(response.json["errors"]["dni"], "El DNI no puede modificarse.")

    def test_modificacion_de_usuario_falla_si_telefono_tiene_letras_espacios_o_simbolos(self):
        self._crear_usuario_con_roles(
            email="admin@centro.test",
            dni="30000001",
            password="123456",
            roles=["administrador"],
        )
        persona = self._crear_usuario_con_roles(
            email="jorge.petri@example.com",
            dni="33333333",
            password="123456",
            roles=["empleado"],
        )
        self._login_admin()

        response = self.client.put(
            f"/api/usuarios/{persona.persona_id}",
            json=self._payload_empleado(telefono="221 444-663A"),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["status"], "validation_error")
        self.assertEqual(
            response.json["errors"]["telefono"],
            "Ingrese un telefono valido sin caracteres especiales, letras o espacios. Ejemplo 2214446633",
        )

    def test_modificacion_de_usuario_falla_si_telefono_no_comienza_con_uno_dos_o_tres(self):
        self._crear_usuario_con_roles(
            email="admin@centro.test",
            dni="30000001",
            password="123456",
            roles=["administrador"],
        )
        persona = self._crear_usuario_con_roles(
            email="jorge.petri@example.com",
            dni="33333333",
            password="123456",
            roles=["socio"],
        )
        self._login_admin()

        response = self.client.put(
            f"/api/usuarios/{persona.persona_id}",
            json=self._payload_empleado(telefono="4221446633"),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["status"], "validation_error")
        self.assertEqual(
            response.json["errors"]["telefono"],
            "Debe ingresar un telefono que comience con 1, 2 ó 3. Ejemplo: 2214446633",
        )

    def test_modificacion_de_usuario_falla_si_telefono_no_alcanza_diez_digitos(self):
        self._crear_usuario_con_roles(
            email="admin@centro.test",
            dni="30000001",
            password="123456",
            roles=["administrador"],
        )
        persona = self._crear_usuario_con_roles(
            email="jorge.petri@example.com",
            dni="33333333",
            password="123456",
            roles=["socio"],
        )
        self._login_admin()

        response = self.client.put(
            f"/api/usuarios/{persona.persona_id}",
            json=self._payload_empleado(telefono="221444663"),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["status"], "validation_error")
        self.assertEqual(
            response.json["errors"]["telefono"],
            "El teléfono debe alcanzar los 10 dígitos totales. Ejemplo: 2214446633",
        )

    def _payload_empleado(self, **overrides):
        payload = {
            "dni": "33333333",
            "email": "jorge.petri@example.com",
            "nombre": "Jorge",
            "apellido": "Petri",
            "telefono": "2215003000",
            "calle": "59",
            "numero_puerta": "326",
            "codigo_postal": "1900",
        }
        payload.update(overrides)
        return payload

    def _login_admin(self):
        response = self.client.post(
            "/api/login",
            json={"email": "admin@centro.test", "password": "123456"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "authenticated")

    def _crear_persona(self, dni, email):
        persona = Persona(
            dni=dni,
            email=email,
            password_hash="hash",
            nombre="Ada",
            apellido="Lovelace",
            telefono="2214446633",
            calle="Calle Falsa",
            numero_puerta="123",
            codigo_postal="1900",
            estado="activo",
        )
        db.session.add(persona)
        db.session.commit()
        return persona

    def _crear_usuario_con_roles(self, *, email, dni, password, roles):
        persona = Persona(
            dni=dni,
            email=email,
            password_hash=bcrypt.generate_password_hash(password).decode("utf-8"),
            nombre="Usuario",
            apellido="Prueba",
            telefono="2214446633",
            calle="23",
            numero_puerta="717",
            codigo_postal="1900",
            estado="activo",
        )
        db.session.add(persona)
        db.session.flush()

        for role_name in roles:
            role = Rol.query.filter_by(nombre=role_name).first()
            if role is None:
                role = self._crear_rol(role_name, commit=False)

            db.session.add(
                PersonaRolPuente(persona_id=persona.persona_id, rol_id=role.rol_id)
            )

            if role_name == "empleado":
                db.session.add(Empleado(persona_id=persona.persona_id))
            if role_name == "socio":
                db.session.add(Socio(persona_id=persona.persona_id))

        db.session.commit()
        return persona

    def test_admin_puede_bloquear_usuario(self):
        self._crear_usuario_con_roles(
            email="admin@centro.test",
            dni="30000001",
            password="123456",
            roles=["administrador"],
        )
        persona = self._crear_usuario_con_roles(
            email="socio@centro.test",
            dni="33333333",
            password="123456",
            roles=["socio"],
        )
        self._login_admin()

        response = self.client.put(
            f"/api/usuarios/{persona.persona_id}/bloquear",
            json={"motivo": "Socio problemático", "devolver_dinero": False},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "ok")
        self.assertIn("bloqueado exitosamente", response.json["message"])
        
        updated_persona = db.session.get(Persona, persona.persona_id)
        self.assertEqual(updated_persona.estado, "bloqueado")
        self.assertEqual(updated_persona.motivo_bloqueo, "Socio problemático")

    def test_admin_puede_desbloquear_usuario(self):
        self._crear_usuario_con_roles(
            email="admin@centro.test",
            dni="30000001",
            password="123456",
            roles=["administrador"],
        )
        persona = self._crear_usuario_con_roles(
            email="socio@centro.test",
            dni="33333333",
            password="123456",
            roles=["socio"],
        )
        persona.estado = "bloqueado"
        persona.motivo_bloqueo = "Socio problemático"
        db.session.commit()
        
        self._login_admin()

        response = self.client.put(f"/api/usuarios/{persona.persona_id}/desbloquear")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "ok")
        
        updated_persona = db.session.get(Persona, persona.persona_id)
        self.assertEqual(updated_persona.estado, "activo")
        self.assertIsNone(updated_persona.motivo_bloqueo)

    @patch("src.core.services.reservas.telegram.enviar_mensaje_telegram")
    @patch("src.core.services.reservas.telegram.crear_confirmacion_turno")
    @patch("src.core.services.usuarios._reintegrar_mercadopago")
    def test_bloqueo_devuelve_mensajes_ordenados_por_clase(
        self,
        mock_reintegrar,
        mock_crear_confirmacion,
        mock_enviar_telegram,
    ):
        mock_crear_confirmacion.return_value = "token-test"
        self._crear_usuario_con_roles(
            email="admin@centro.test",
            dni="30000001",
            password="123456",
            roles=["administrador"],
        )
        persona = self._crear_usuario_con_roles(
            email="socio@centro.test",
            dni="33333333",
            password="123456",
            roles=["socio"],
        )
        persona.nombre = "Juan"
        persona.apellido = "Perez"
        socio_espera = self._crear_usuario_con_roles(
            email="espera@centro.test",
            dni="33333334",
            password="123456",
            roles=["socio"],
        )
        socio_espera.nombre = "Jorge"
        socio_espera.apellido = "Fernandez"

        clase = self._crear_clase_para_bloqueo(
            actividad=ActividadEnum.VOLEY,
            fecha=date(2026, 6, 24),
            horario_inicio=time(18, 0),
        )
        reserva = self._crear_reserva_confirmada(persona.persona_id, clase.clase_id)
        self._crear_pago_aprobado(persona.persona_id, reserva.reserva_id, Decimal("5000.00"))
        db.session.add(
            ListaEspera(
                clase_id=clase.clase_id,
                socio_id=socio_espera.persona_id,
                posicion=1,
                estado="pendiente",
            )
        )
        db.session.commit()

        self._login_admin()

        response = self.client.put(
            f"/api/usuarios/{persona.persona_id}/bloquear",
            json={"motivo": "Socio Problematico", "devolver_dinero": True},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json["messages"],
            [
                "El usuario Juan Perez ha sido bloqueado exitosamente. Motivo: Socio Problematico",
                "Se le han devuelto $5000 por la calse de Volley a las 18:00 el dia 24/06/26.",
                'Se ha asignado el cupo de la clase de "Volley" de las "18:00" el dia "24/06/26" al siguiente en la lista de espera. Socio: Jorge Fernandez',
            ],
        )
        self.assertEqual(db.session.get(Reserva, reserva.reserva_id).estado, "cancelada")
        self.assertEqual(
            ListaEspera.query.filter_by(socio_id=socio_espera.persona_id).first().estado,
            "notificado",
        )
        mock_reintegrar.assert_called_once()
        mock_enviar_telegram.assert_called_once()

    def test_bloqueo_falla_si_no_ingresa_motivo_con_nombre_del_usuario(self):
        self._crear_usuario_con_roles(
            email="admin@centro.test",
            dni="30000001",
            password="123456",
            roles=["administrador"],
        )
        persona = self._crear_usuario_con_roles(
            email="socio@centro.test",
            dni="33333333",
            password="123456",
            roles=["socio"],
        )
        persona.nombre = "Juan"
        persona.apellido = "Perez"
        db.session.commit()
        self._login_admin()

        response = self.client.put(
            f"/api/usuarios/{persona.persona_id}/bloquear",
            json={"motivo": "   "},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json["errors"]["motivo"],
            "Debe ingresar un motivo de bloqueo para poder bloquear al usuario Juan Perez",
        )

    def test_desbloquear_usuario_informa_si_no_presentaba_sanciones(self):
        self._crear_usuario_con_roles(
            email="admin@centro.test",
            dni="30000001",
            password="123456",
            roles=["administrador"],
        )
        persona = self._crear_usuario_con_roles(
            email="socio@centro.test",
            dni="33333333",
            password="123456",
            roles=["socio"],
        )
        persona.estado = "bloqueado"
        persona.motivo_bloqueo = "Socio Problematico"
        db.session.commit()

        self._login_admin()

        response = self.client.put(f"/api/usuarios/{persona.persona_id}/desbloquear")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json["message"],
            "El usuario ha sido desbloqueado exitosamente. No presentaba sanciones.",
        )

    def test_desbloquear_usuario_reinicia_sanciones_y_muestra_mensaje(self):
        self._crear_usuario_con_roles(
            email="admin@centro.test",
            dni="30000001",
            password="123456",
            roles=["administrador"],
        )
        persona = self._crear_usuario_con_roles(
            email="socio@centro.test",
            dni="33333333",
            password="123456",
            roles=["socio"],
        )
        persona.estado = "bloqueado"
        persona.motivo_bloqueo = "Socio Problematico"
        persona.socio.descuento_bloqueado_hasta = date.today() + timedelta(days=30)
        db.session.commit()

        self._login_admin()

        response = self.client.put(f"/api/usuarios/{persona.persona_id}/desbloquear")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json["message"],
            "El usuario ha sido desbloqueado exitosamente. Presentaba sanciones",
        )

        updated_persona = db.session.get(Persona, persona.persona_id)
        self.assertEqual(updated_persona.estado, "activo")
        self.assertIsNone(updated_persona.socio.descuento_bloqueado_hasta)

    def _crear_clase_para_bloqueo(self, *, actividad, fecha, horario_inicio):
        profesor = Profesor(nombre="Profesor Bloqueo", dni="99988877", telefono="2210001111")
        db.session.add(profesor)
        db.session.flush()

        clase = Clase(
            actividad=actividad,
            fecha=fecha,
            horario_inicio=horario_inicio,
            horario_fin=time((horario_inicio.hour + 1) % 24, horario_inicio.minute),
            cancha="Cancha Test",
            nivel=NivelEnum.PRINCIPIANTE,
            cupos=1,
            precio=Decimal("5000.00"),
            tipo_clase=TipoClaseEnum.PARTICULAR,
            profesor_id=profesor.profesor_id,
        )
        db.session.add(clase)
        db.session.flush()
        return clase

    def _crear_reserva_confirmada(self, socio_id, clase_id):
        reserva = Reserva(
            socio_id=socio_id,
            clase_id=clase_id,
            tipo_reserva="estandar",
            estado="confirmada",
            creada_en=datetime.now(timezone.utc),
            confirmada_en=datetime.now(timezone.utc),
        )
        db.session.add(reserva)
        db.session.flush()
        return reserva

    def _crear_pago_aprobado(self, socio_id, reserva_id, monto):
        pago = Pago(
            socio_id=socio_id,
            reserva_id=reserva_id,
            proveedor="mercadopago",
            external_ref=f"test-{reserva_id}",
            monto_bruto=monto,
            descuento_pct=Decimal("0"),
            monto_pagado=monto,
            estado="aprobado",
            fecha_pago=datetime.now(timezone.utc),
        )
        db.session.add(pago)
        db.session.flush()
        return pago

    def _crear_rol(self, nombre, commit=True):
        role = Rol(nombre=nombre, descripcion=f"Rol {nombre}")
        db.session.add(role)
        db.session.flush()
        if commit:
            db.session.commit()
        return role
