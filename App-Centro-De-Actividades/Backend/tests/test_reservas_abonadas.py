import unittest
from datetime import date, datetime, time, timezone
from decimal import Decimal

from src.core.bcrypt_and_session import bcrypt
from src.core.database import db
from src.core.enums.clase_enum import ActividadEnum, NivelEnum, TipoClaseEnum
from src.core.models.abono_mensual import AbonoMensual
from src.core.models.clase import Clase
from src.core.models.pago import Pago
from src.core.models.persona import Persona, PersonaRolPuente, Rol, Socio
from src.core.models.profesor import Profesor
from src.core.models.reserva import Reserva
from src.core.seeds.usuarios import DEFAULT_PASSWORD
from src.core.services import reservas as reservas_service
from src.web import create_app


class ReservasAbonadasTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()
        self.original_now = reservas_service._now
        reservas_service._now = lambda: datetime(2026, 6, 5, 12, 0, tzinfo=timezone.utc)

    def tearDown(self):
        reservas_service._now = self.original_now
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_reserva_abonada_aplica_descuento_y_confirma_cuatro_clases(self):
        socio = self._crear_socio("abonado@centro.test", "40111111")
        clases = self._crear_clases_consecutivas()
        self._login(socio.email)

        response = self.client.post("/api/reservas/abonada", json={"clase_id": clases[0].clase_id})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "payment_required")
        self.assertEqual(response.json["descuento_pct"], "20.00")

        pago = Pago.query.one()
        self.assertEqual(pago.monto_bruto, Decimal("4000.00"))
        self.assertEqual(pago.descuento_pct, Decimal("20.00"))

        retorno = self.client.post(
            "/api/reservas/espontanea/pago-retorno",
            json={"reserva_id": response.json["reserva_id"], "status": "approved"},
        )

        self.assertEqual(retorno.status_code, 200)
        self.assertEqual(retorno.json["message"], "Reserva abonada confirmada.")

        reservas = Reserva.query.order_by(Reserva.reserva_id.asc()).all()
        self.assertEqual(len(reservas), 4)
        self.assertTrue(all(reserva.estado == "confirmada" for reserva in reservas))
        self.assertTrue(all(reserva.tipo_reserva == "abonada" for reserva in reservas))

        abono = AbonoMensual.query.one()
        self.assertEqual(abono.estado, "activo")
        self.assertFalse(abono.prioridad_renovacion)
        self.assertEqual(abono.descuento_aplicado_pct, Decimal("20.00"))

        db.session.refresh(pago)
        self.assertEqual(pago.estado, "aprobado")
        self.assertEqual(pago.monto_pagado, Decimal("3200.00"))

    def test_reserva_abonada_sancionada_no_aplica_descuento(self):
        socio = self._crear_socio("sancionado@centro.test", "40222222")
        socio.socio.descuento_bloqueado_hasta = date(2026, 6, 30)
        db.session.commit()
        clases = self._crear_clases_consecutivas()
        self._login(socio.email)

        response = self.client.post("/api/reservas/abonada", json={"clase_id": clases[0].clase_id})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["descuento_pct"], "0.00")
        self.assertEqual(response.json["monto_a_cobrar"], "4000.00")
        self.assertIn("No se aplicó descuento por sanción", response.json["message"])

    def test_reserva_abonada_falla_si_alguna_clase_no_tiene_cupo(self):
        socio = self._crear_socio("sin-cupo@centro.test", "40333333")
        otro_socio = self._crear_socio("ocupante@centro.test", "40444444")
        clases = self._crear_clases_consecutivas(cupos=1)
        db.session.add(
            Reserva(
                clase_id=clases[2].clase_id,
                socio_id=otro_socio.persona_id,
                tipo_reserva="espontanea",
                estado="confirmada",
            )
        )
        db.session.commit()
        self._login(socio.email)

        response = self.client.post("/api/reservas/abonada", json={"clase_id": clases[0].clase_id})

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json["status"], "no_cupo")
        self.assertEqual(Reserva.query.filter_by(socio_id=socio.persona_id).count(), 0)

    def _crear_socio(self, email, dni):
        persona = Persona(
            dni=dni,
            email=email,
            password_hash=bcrypt.generate_password_hash(DEFAULT_PASSWORD).decode("utf-8"),
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
        db.session.add(Socio(persona_id=persona.persona_id))

        role = Rol.query.filter_by(nombre="socio").first()
        if role is None:
            role = Rol(nombre="socio", descripcion="Rol socio")
            db.session.add(role)
            db.session.flush()

        db.session.add(PersonaRolPuente(persona_id=persona.persona_id, rol_id=role.rol_id))
        db.session.commit()
        return persona

    def _crear_clases_consecutivas(self, cupos=8):
        profesor = Profesor(nombre="Profesor Abono", dni="99887766", telefono="2215000000")
        db.session.add(profesor)
        db.session.flush()

        fechas = [date(2026, 6, 10), date(2026, 6, 17), date(2026, 6, 24), date(2026, 7, 1)]
        clases = []
        for fecha in fechas:
            clase = Clase(
                actividad=ActividadEnum.FUTBOL,
                fecha=fecha,
                horario_inicio=time(19, 0),
                horario_fin=time(20, 0),
                cancha="Cancha 1",
                nivel=NivelEnum.PRINCIPIANTE,
                cupos=cupos,
                precio=Decimal("1000.00"),
                tipo_clase=TipoClaseEnum.GRUPAL,
                profesor_id=profesor.profesor_id,
            )
            db.session.add(clase)
            clases.append(clase)

        db.session.commit()
        return clases

    def _login(self, email):
        self.client.post("/api/login", json={"email": email, "password": DEFAULT_PASSWORD})


if __name__ == "__main__":
    unittest.main()
