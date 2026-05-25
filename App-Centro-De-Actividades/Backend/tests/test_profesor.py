import unittest

from src.core.database import db
from src.core.models.profesor import Profesor
from src.web import create_app


class ProfesorTestCase(unittest.TestCase):
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

    def test_crear_profesor_exitoso(self):
        response = self.client.post("/api/profesor/crear", json=self._payload())

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["message"], "El profesor fue cargado correctamente")

        profesor = Profesor.query.filter_by(dni="45678876").first()
        self.assertIsNotNone(profesor)
        self.assertEqual(profesor.telefono, "1156022756")

    def test_crear_profesor_falla_si_telefono_contiene_letras_espacios_o_simbolos(self):
        response = self.client.post(
            "/api/profesor/crear",
            json=self._payload(telefono="221 444-663A"),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["status"], "validation_error")
        self.assertEqual(
            response.json["errors"]["telefono"],
            "Ingrese un telefono valido sin caracteres especiales, letras o espacios. Ejemplo 2214446633",
        )

    def test_crear_profesor_falla_si_telefono_no_comienza_con_uno_dos_o_tres(self):
        response = self.client.post(
            "/api/profesor/crear",
            json=self._payload(telefono="4221446633"),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["status"], "validation_error")
        self.assertEqual(
            response.json["errors"]["telefono"],
            "Debe ingresar un telefono que comience con 1, 2 ó 3. Ejemplo: 2214446633",
        )

    def test_crear_profesor_falla_si_telefono_no_alcanza_los_diez_digitos(self):
        response = self.client.post(
            "/api/profesor/crear",
            json=self._payload(telefono="221444663"),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["status"], "validation_error")
        self.assertEqual(
            response.json["errors"]["telefono"],
            "El teléfono debe alcanzar los 10 dígitos totales. Ejemplo: 2214446633",
        )

    def _payload(self, **overrides):
        payload = {
            "nombre": "Carlos",
            "dni": "45678876",
            "telefono": "1156022756",
        }
        payload.update(overrides)
        return payload
