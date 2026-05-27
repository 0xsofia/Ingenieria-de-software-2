import unittest
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

from src.core.database import db
from src.core.models.clase import Clase
from src.core.models.persona import Persona
from src.core.models.reserva import Reserva
from src.core.seeds.clases import _build_dynamic_clases_to_seed, seed_clases
from src.core.seeds.profesores import seed_profesores
from src.core.seeds.reservas import seed_reservas
from src.core.seeds.usuarios import seed_usuarios
from src.web import create_app


SEED_TIME = datetime(2026, 5, 26, 8, 7, tzinfo=ZoneInfo("America/Argentina/Buenos_Aires"))
UTC_EQUIVALENT_SEED_TIME = datetime(2026, 5, 27, 0, 12, tzinfo=timezone.utc)


class SeedClasesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_seed_clases_crea_cuatro_clases_dinamicas_para_la_hora_actual(self):
        seed_profesores()
        seed_clases(SEED_TIME)

        clases = Clase.query.order_by(Clase.fecha, Clase.horario_inicio).all()

        self.assertEqual(len(clases), 5)
        self.assertEqual(
            [clase.horario_inicio for clase in clases],
            [time(7, 0), time(8, 0), time(8, 15), time(8, 30), time(9, 0)],
        )
        self.assertEqual(clases[0].actividad.value, "Voley")
        self.assertEqual(clases[0].cupos, 1)
        self.assertEqual(clases[1].actividad.value, "Voley")
        self.assertEqual(clases[1].cupos, 8)
        self.assertTrue(all(clase.fecha.isoformat() == "2026-05-26" for clase in clases))

    def test_seed_clases_toma_horario_argentina_aunque_el_servidor_este_en_utc(self):
        clases = _build_dynamic_clases_to_seed(UTC_EQUIVALENT_SEED_TIME)

        self.assertEqual(
            [clase_data["horario_inicio"] for clase_data in clases],
            ["20:00", "21:00", "21:15", "21:30", "22:00"],
        )
        self.assertTrue(all(clase_data["fecha"] == "2026-05-26" for clase_data in clases))

    def test_seed_db_reserva_todas_las_clases_dinamicas_para_socio_centro(self):
        seed_usuarios()
        seed_profesores()
        seed_clases(SEED_TIME)
        seed_reservas(SEED_TIME)

        persona = Persona.query.filter_by(email="socio@centro.test").first()
        reservas = (
            Reserva.query.filter_by(socio_id=persona.persona_id)
            .join(Clase, Reserva.clase_id == Clase.clase_id)
            .order_by(Clase.fecha, Clase.horario_inicio)
            .all()
        )

        self.assertIsNotNone(persona)
        self.assertEqual(len(reservas), 5)
        self.assertEqual(
            [reserva.clase.horario_inicio for reserva in reservas],
            [time(7, 0), time(8, 0), time(8, 15), time(8, 30), time(9, 0)],
        )
        self.assertTrue(all(reserva.estado == "confirmada" for reserva in reservas))
        self.assertTrue(all(reserva.tipo_reserva == "estandar" for reserva in reservas))
