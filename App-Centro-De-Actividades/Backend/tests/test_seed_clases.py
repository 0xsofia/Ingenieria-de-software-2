import unittest
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

from src.core.database import db
from src.core.models.clase import Clase
from src.core.models.persona import Persona
from src.core.models.reserva import Reserva
from src.core.seeds import run_seeds
from src.core.seeds.clases import (
    _build_abono_mensual_clases_to_seed,
    _build_dynamic_clases_to_seed,
    seed_clases,
    seed_clases_abono_mensual,
)
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

    def test_seed_clases_crea_cinco_clases_dinamicas_para_la_hora_actual(self):
        seed_profesores()
        seed_clases(SEED_TIME)

        clases = Clase.query.order_by(Clase.fecha, Clase.horario_inicio).all()

        self.assertEqual(len(clases), 9)
        self.assertEqual(
            [clase.horario_inicio for clase in clases[:7]],
            [time(7, 0), time(8, 0), time(8, 15), time(8, 30), time(8, 45), time(9, 0), time(9, 15)],
        )
        self.assertEqual(clases[0].actividad.value, "Voley")
        self.assertEqual(clases[0].cupos, 1)
        self.assertEqual(clases[1].actividad.value, "Voley")
        self.assertEqual(clases[1].cupos, 8)
        self.assertEqual(clases[5].cupos, 1)
        self.assertEqual(clases[6].actividad.value, "Padel")
        self.assertEqual(clases[6].cupos, 9)
        self.assertEqual(
            [clase.fecha.isoformat() for clase in clases],
            [
                "2026-05-26",
                "2026-05-26",
                "2026-05-26",
                "2026-05-26",
                "2026-05-26",
                "2026-05-26",
                "2026-05-26",
                "2026-05-27",
                "2026-05-28",
            ],
        )
        self.assertEqual(clases[7].horario_inicio, time(8, 30))
        self.assertEqual(clases[8].horario_inicio, time(20, 0))

    def test_seed_clases_toma_horario_argentina_aunque_el_servidor_este_en_utc(self):
        clases = _build_dynamic_clases_to_seed(UTC_EQUIVALENT_SEED_TIME)

        self.assertEqual(
            [clase_data["horario_inicio"] for clase_data in clases],
            ["20:00", "21:00", "21:15", "21:30", "21:45", "22:00", "22:15", "21:30", "09:00"],
        )
        self.assertEqual(
            [clase_data["fecha"] for clase_data in clases],
            [
                "2026-05-26",
                "2026-05-26",
                "2026-05-26",
                "2026-05-26",
                "2026-05-26",
                "2026-05-26",
                "2026-05-26",
                "2026-05-27",
                "2026-05-29",
            ],
        )

    def test_seed_clases_abono_mensual_crea_cuatro_miercoles_del_mes_proximo(self):
        seed_profesores()
        seed_clases_abono_mensual(SEED_TIME)

        clases = Clase.query.order_by(Clase.fecha, Clase.horario_inicio).all()

        self.assertEqual(len(clases), 4)
        self.assertEqual([clase.actividad.value for clase in clases], ["Futbol"] * 4)
        self.assertEqual([clase.horario_inicio for clase in clases], [time(19, 0)] * 4)
        self.assertEqual([clase.cupos for clase in clases], [8] * 4)
        self.assertEqual(
            [clase.fecha.isoformat() for clase in clases],
            ["2026-06-03", "2026-06-10", "2026-06-17", "2026-06-24"],
        )

    def test_build_clases_abono_mensual_toma_mes_proximo_en_horario_argentina(self):
        clases = _build_abono_mensual_clases_to_seed(UTC_EQUIVALENT_SEED_TIME)

        self.assertEqual(
            [clase_data["fecha"] for clase_data in clases],
            ["2026-06-03", "2026-06-10", "2026-06-17", "2026-06-24"],
        )
        self.assertEqual([clase_data["horario_inicio"] for clase_data in clases], ["19:00"] * 4)

    def test_seed_db_reserva_clases_dinamicas_habilitadas_para_socio_centro(self):
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
        self.assertEqual(len(reservas), 8)
        self.assertEqual(
            [reserva.clase.horario_inicio for reserva in reservas],
            [time(7, 0), time(8, 0), time(8, 15), time(8, 30), time(8, 45), time(9, 0), time(8, 30), time(20, 0)],
        )
        self.assertTrue(all(reserva.estado == "confirmada" for reserva in reservas))
        self.assertTrue(all(reserva.tipo_reserva == "estandar" for reserva in reservas))

    def test_run_seeds_no_crea_clases_extra_fuera_del_seed_base(self):
        run_seeds(self.app)

        clases = Clase.query.order_by(Clase.fecha, Clase.horario_inicio).all()

        self.assertEqual(len(clases), 13)
