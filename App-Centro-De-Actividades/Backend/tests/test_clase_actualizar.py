import unittest
from datetime import date, time

from src.core.database import db
from src.core.enums.clase_enum import ActividadEnum, NivelEnum, TipoClaseEnum
from src.core.models.clase import Clase
from src.core.models.persona import Persona, Socio
from src.core.models.profesor import Profesor
from src.core.models.reserva import Reserva
from src.web import create_app


class ClaseActualizarTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _crear_profesor(self, nombre, dni):
        profesor = Profesor(nombre=nombre, dni=dni, telefono='2215000000')
        db.session.add(profesor)
        db.session.commit()
        return profesor

    def _crear_socio(self, dni, email):
        persona = Persona(
            dni=dni,
            email=email,
            password_hash='testpassword',
            nombre='Socio',
            apellido='Prueba',
            telefono='2215000001',
            calle='Calle Falsa',
            numero_puerta='123',
            codigo_postal='1900',
        )
        db.session.add(persona)
        db.session.flush()
        socio = Socio(persona_id=persona.persona_id)
        db.session.add(socio)
        db.session.commit()
        return socio

    def _crear_clase(self, profesor_id, fecha, horario_inicio, horario_fin, cupos=20):
        clase = Clase(
            actividad=ActividadEnum.VOLEY,
            fecha=fecha,
            horario_inicio=horario_inicio,
            horario_fin=horario_fin,
            cancha='Cancha 1',
            nivel=NivelEnum.INTERMEDIO,
            cupos=cupos,
            precio=200,
            tipo_clase=TipoClaseEnum.GRUPAL,
            profesor_id=profesor_id,
        )
        db.session.add(clase)
        db.session.commit()
        return clase

    def _crear_reserva(self, socio_id, clase_id, estado='confirmada'):
        reserva = Reserva(
            clase_id=clase_id,
            socio_id=socio_id,
            tipo_reserva='estandar',
            estado=estado,
        )
        db.session.add(reserva)
        db.session.commit()
        return reserva

    def test_actualizar_clase_exitoso(self):
        profesor = self._crear_profesor('Carlos', '11111111')
        clase = self._crear_clase(
            profesor_id=profesor.profesor_id,
            fecha=date.today(),
            horario_inicio=time(19, 0),
            horario_fin=time(20, 0),
            cupos=20,
        )

        response = self.client.put(
            f'/api/clase/{clase.clase_id}/actualizar',
            json={
                'actividad': 'Voley',
                'fecha': clase.fecha.strftime('%Y-%m-%d'),
                'horario_inicio': 12,
                'cancha': clase.cancha,
                'nivel': 'Intermedio',
                'cupos': 20,
                'precio': 200,
                'profesor_id': profesor.profesor_id,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['message'], 'La clase fue actualizada correctamente.')

        clase_actualizada = Clase.query.get(clase.clase_id)
        self.assertEqual(clase_actualizada.horario_inicio, time(12, 0))
        self.assertEqual(clase_actualizada.horario_fin, time(13, 0))

    def test_actualizar_clase_falla_por_superposicion_horaria(self):
        profesor = self._crear_profesor('Carlos', '22222222')
        clase_actual = self._crear_clase(
            profesor_id=profesor.profesor_id,
            fecha=date.today(),
            horario_inicio=time(19, 0),
            horario_fin=time(20, 0),
            cupos=20,
        )
        self._crear_clase(
            profesor_id=profesor.profesor_id,
            fecha=date.today(),
            horario_inicio=time(16, 0),
            horario_fin=time(17, 0),
            cupos=20,
        )

        response = self.client.put(
            f'/api/clase/{clase_actual.clase_id}/actualizar',
            json={
                'actividad': 'Voley',
                'fecha': clase_actual.fecha.strftime('%Y-%m-%d'),
                'horario_inicio': 16,
                'cancha': clase_actual.cancha,
                'nivel': 'Intermedio',
                'cupos': 20,
                'precio': 200,
                'profesor_id': profesor.profesor_id,
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json['message'],
            'No puede actualizarse la clase ya que el profesor tiene superposición horaria con otra clase',
        )

    def test_actualizar_clase_falla_por_superposicion_al_cambiar_profesor(self):
        profesor_carlos = self._crear_profesor('Carlos', '33333333')
        profesor_clemente = self._crear_profesor('Clemente', '44444444')

        clase_actual = self._crear_clase(
            profesor_id=profesor_carlos.profesor_id,
            fecha=date.today(),
            horario_inicio=time(19, 0),
            horario_fin=time(20, 0),
            cupos=20,
        )
        self._crear_clase(
            profesor_id=profesor_clemente.profesor_id,
            fecha=date.today(),
            horario_inicio=time(19, 0),
            horario_fin=time(20, 0),
            cupos=20,
        )

        response = self.client.put(
            f'/api/clase/{clase_actual.clase_id}/actualizar',
            json={
                'actividad': 'Voley',
                'fecha': clase_actual.fecha.strftime('%Y-%m-%d'),
                'horario_inicio': 19,
                'cancha': clase_actual.cancha,
                'nivel': 'Intermedio',
                'cupos': 20,
                'precio': 200,
                'profesor_id': profesor_clemente.profesor_id,
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json['message'],
            'No puede actualizarse la clase ya que el profesor tiene superposición horaria con otra clase',
        )

    def test_actualizar_clase_falla_por_cupos_menores_a_reservas(self):
        profesor = self._crear_profesor('Carlos', '55555555')
        clase_actual = self._crear_clase(
            profesor_id=profesor.profesor_id,
            fecha=date.today(),
            horario_inicio=time(19, 0),
            horario_fin=time(20, 0),
            cupos=20,
        )

        socio = self._crear_socio('66666666', 'socio@test.com')
        segundo_socio = self._crear_socio('77777777', 'socio2@test.com')
        self._crear_reserva(socio.persona_id, clase_actual.clase_id)
        self._crear_reserva(segundo_socio.persona_id, clase_actual.clase_id)

        response = self.client.put(
            f'/api/clase/{clase_actual.clase_id}/actualizar',
            json={
                'actividad': 'Voley',
                'fecha': clase_actual.fecha.strftime('%Y-%m-%d'),
                'horario_inicio': 19,
                'cancha': clase_actual.cancha,
                'nivel': 'Intermedio',
                'cupos': 2,
                'precio': 200,
                'profesor_id': profesor.profesor_id,
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json['message'],
            'La cantidad de cupos debe ser mayor o igual a la cantidad de reservas asociadas',
        )
