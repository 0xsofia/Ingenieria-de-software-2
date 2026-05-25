import unittest

from src.core.database import db
from src.core.models.persona import Persona, PersonaRolPuente, Rol, Socio
from src.web import create_app


class RegistrarseTestCase(unittest.TestCase):
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

    def test_registro_exitoso_crea_persona_socio_y_rol(self):
        socio_role = self._crear_rol("socio")

        response = self.client.post("/api/registrarse", json=self._payload())

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["status"], "registered")
        self.assertEqual(response.json["redirect_to"], "/login")

        persona = Persona.query.filter_by(email="tomas.f@example.com").first()
        self.assertIsNotNone(persona)
        self.assertEqual(persona.dni, "11111111")
        self.assertEqual(persona.telefono, "2214446633")
        self.assertIsNotNone(db.session.get(Socio, persona.persona_id))
        self.assertIsNotNone(
            PersonaRolPuente.query.filter_by(
                persona_id=persona.persona_id, rol_id=socio_role.rol_id
            ).first()
        )

    def test_registro_exitoso_con_telefono_que_comienza_con_dos(self):
        self._crear_rol("socio")

        response = self.client.post(
            "/api/registrarse",
            json=self._payload(
                dni="12345678", email="codigo4@example.com", telefono="2221446633"
            ),
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["status"], "registered")

        persona = Persona.query.filter_by(email="codigo4@example.com").first()
        self.assertIsNotNone(persona)
        self.assertEqual(persona.telefono, "2221446633")

    def test_registro_falla_si_dni_ya_existe(self):
        self._crear_rol("socio")
        self._crear_persona(dni="11111111", email="existente@example.com")

        response = self.client.post(
            "/api/registrarse",
            json=self._payload(email="nuevo@example.com"),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["status"], "validation_error")
        self.assertEqual(
            response.json["errors"]["dni"],
            "El DNI ya se encuentra registrado en el sistema.",
        )

    def test_registro_falla_si_email_ya_existe(self):
        self._crear_rol("socio")
        self._crear_persona(dni="22222222", email="tomas.f@example.com")

        response = self.client.post(
            "/api/registrarse",
            json=self._payload(dni="99999999"),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["status"], "validation_error")
        self.assertEqual(
            response.json["errors"]["email"],
            "El email ya se encuentra registrado en el sistema.",
        )

    def test_registro_falla_si_repeat_password_no_coincide(self):
        self._crear_rol("socio")

        response = self.client.post(
            "/api/registrarse",
            json=self._payload(repeat_password="otra-clave"),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["status"], "validation_error")
        self.assertEqual(
            response.json["errors"]["repeat_password"],
            "Repetir contraseña debe coincidir con la contraseña.",
        )

    def test_registro_falla_si_password_no_tiene_longitud_valida(self):
        self._crear_rol("socio")

        response = self.client.post(
            "/api/registrarse",
            json=self._payload(password="12345", repeat_password="12345"),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["status"], "validation_error")
        self.assertEqual(
            response.json["errors"]["password"],
            "La contraseña debe tener entre 6 a 12 caracteres.",
        )

    def test_registro_falla_si_telefono_contiene_letras_espacios_o_simbolos(self):
        self._crear_rol("socio")

        response = self.client.post(
            "/api/registrarse",
            json=self._payload(telefono="221 444-663A"),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["status"], "validation_error")
        self.assertEqual(
            response.json["errors"]["telefono"],
            "Ingrese un telefono valido sin caracteres especiales, letras o espacios. Ejemplo 2214446633",
        )

    def test_registro_falla_si_telefono_no_comienza_con_uno_dos_o_tres(self):
        self._crear_rol("socio")

        response = self.client.post(
            "/api/registrarse",
            json=self._payload(telefono="4221446633"),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["status"], "validation_error")
        self.assertEqual(
            response.json["errors"]["telefono"],
            "Debe ingresar un telefono que comience con 1, 2 ó 3. Ejemplo: 2214446633",
        )

    def test_registro_falla_si_telefono_no_alcanza_los_diez_digitos(self):
        self._crear_rol("socio")

        response = self.client.post(
            "/api/registrarse",
            json=self._payload(telefono="221444663"),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["status"], "validation_error")
        self.assertEqual(
            response.json["errors"]["telefono"],
            "El teléfono debe alcanzar los 10 dígitos totales. Ejemplo: 2214446633",
        )

    def test_registro_falla_si_falta_rol_socio(self):
        response = self.client.post("/api/registrarse", json=self._payload())

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json["status"], "error")
        self.assertIn("rol socio", response.json["message"])

    def _payload(self, **overrides):
        payload = {
            "dni": "11111111",
            "email": "tomas.f@example.com",
            "nombre": "Tomas",
            "apellido": "Fernandez",
            "telefono": "2214446633",
            "calle": "23",
            "numero_puerta": "717",
            "codigo_postal": "1900",
            "password": "123456",
            "repeat_password": "123456",
        }
        payload.update(overrides)
        return payload

    def _crear_persona(self, dni, email):
        persona = Persona(
            dni=dni,
            email=email,
            password_hash="hash",
            nombre="Ada",
            apellido="Lovelace",
            telefono="0111512345678",
            calle="Calle Falsa",
            numero_puerta="123",
            codigo_postal="1900",
            estado="activo",
        )
        db.session.add(persona)
        db.session.commit()
        return persona

    def _crear_rol(self, nombre):
        role = Rol(nombre=nombre, descripcion=f"Rol {nombre}")
        db.session.add(role)
        db.session.commit()
        return role
