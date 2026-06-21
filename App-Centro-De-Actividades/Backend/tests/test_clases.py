import unittest
from datetime import datetime, time, timedelta

from src.core.database import db
from src.core.enums.clase_enum import ActividadEnum, NivelEnum, TipoClaseEnum
from src.core.models.clase import Clase
from src.core.models.profesor import Profesor
from src.core.services.clase_service import crear_clase_completa, validar_payload_clase
from src.web import create_app


class ClasesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        self.profesor = Profesor(
            nombre="Carlos",
            dni="12345678",
            telefono="2215003101",
        )
        db.session.add(self.profesor)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_crea_cuatro_clases_del_mes_para_dia_de_semana(self):
        payload, errors = validar_payload_clase(self._payload())
        self.assertEqual(errors, {})

        body, status = crear_clase_completa(
            payload,
            fecha_actual=datetime(2026, 6, 1, 12, 0),
        )

        self.assertEqual(status, 201)
        self.assertEqual(body["message"], "La clase ha sido creada con éxito.")
        self.assertEqual(body["clases_creadas"], 4)

        clases = Clase.query.order_by(Clase.fecha).all()
        self.assertEqual(
            [clase.fecha.isoformat() for clase in clases],
            ["2026-06-02", "2026-06-09", "2026-06-16", "2026-06-23"],
        )
        self.assertTrue(all(clase.horario_inicio == time(19, 0) for clase in clases))
        self.assertTrue(all(clase.horario_fin == time(20, 0) for clase in clases))
        self.assertTrue(all(clase.tipo_clase == TipoClaseEnum.GRUPAL for clase in clases))

    def test_falla_si_profesor_tiene_superposicion_horaria(self):
        self._crear_clase_existente(datetime(2026, 6, 16).date(), time(19, 0))
        payload, errors = validar_payload_clase(
            self._payload(actividad="Futbol", nivel="Avanzado", precio=2300)
        )
        self.assertEqual(errors, {})

        body, status = crear_clase_completa(
            payload,
            fecha_actual=datetime(2026, 6, 1, 12, 0),
        )

        self.assertEqual(status, 400)
        self.assertEqual(
            body["message"],
            "No se puede registrar la clase, el profesor tiene superposición horaria con otra clase",
        )
        self.assertEqual(Clase.query.count(), 1)

    def test_falla_si_dia_y_horario_del_mes_no_estan_vigentes(self):
        payload, errors = validar_payload_clase(
            self._payload(
                actividad="Futbol",
                dia_semana="Miércoles",
                horario_inicio=9,
                nivel="Avanzado",
            )
        )
        self.assertEqual(errors, {})

        body, status = crear_clase_completa(
            payload,
            fecha_actual=datetime(2026, 6, 25, 12, 0),
        )

        self.assertEqual(status, 400)
        self.assertEqual(
            body["message"],
            "No se pudo registrar la clase, el día y horario seleccionados ya no son vigentes",
        )
        self.assertEqual(Clase.query.count(), 0)

    def test_permite_clase_a_las_cero_si_otra_finaliza_a_las_cero(self):
        self._crear_clase_existente(datetime(2026, 6, 1).date(), time(23, 0))
        payload, errors = validar_payload_clase(
            self._payload(dia_semana="Martes", horario_inicio=0)
        )
        self.assertEqual(errors, {})

        body, status = crear_clase_completa(
            payload,
            fecha_actual=datetime(2026, 6, 1, 12, 0),
        )

        self.assertEqual(status, 201)
        self.assertEqual(body["clases_creadas"], 4)

        clases_cero = Clase.query.filter_by(horario_inicio=time(0, 0)).all()
        self.assertEqual(len(clases_cero), 4)
        self.assertTrue(all(clase.horario_fin == time(1, 0) for clase in clases_cero))

    def _payload(self, **overrides):
        payload = {
            "actividad": "Voley",
            "dia_semana": "Martes",
            "mes": "Junio",
            "horario_inicio": 19,
            "cancha": "Voley",
            "nivel": "Principiante",
            "cupos": 10,
            "precio": 1000,
            "profesor_id": self.profesor.profesor_id,
        }
        payload.update(overrides)
        return payload

    def _crear_clase_existente(self, fecha, horario_inicio):
        clase = Clase(
            actividad=ActividadEnum.VOLEY,
            fecha=fecha,
            horario_inicio=horario_inicio,
            horario_fin=(datetime.combine(fecha, horario_inicio) + timedelta(hours=1)).time(),
            cancha="Voley",
            nivel=NivelEnum.PRINCIPIANTE,
            cupos=10,
            precio=1000,
            tipo_clase=TipoClaseEnum.GRUPAL,
            profesor_id=self.profesor.profesor_id,
        )
        db.session.add(clase)
        db.session.commit()
        return clase
