import unittest
from datetime import date, time

from src.core.bcrypt_and_session import bcrypt
from src.core.database import db
from src.core.enums.clase_enum import ActividadEnum, NivelEnum, TipoClaseEnum
from src.core.models.clase import Clase
from src.core.models.persona import Empleado, Persona, PersonaRolPuente, Rol, Socio
from src.core.models.profesor import Profesor
from src.core.models.reserva import Reserva
from src.core.seeds.usuarios import DEFAULT_PASSWORD
from src.web import create_app


class AsistenciasTestCase(unittest.TestCase):
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

    def test_socio_no_puede_escanear_qr_de_otro_socio(self):
        socio_actor = self._crear_persona(
            email="actor@centro.test",
            dni="30000011",
            password=DEFAULT_PASSWORD,
            roles={"socio": []},
            como_socio=True,
        )
        socio_duenio = self._crear_persona(
            email="duenio@centro.test",
            dni="30000012",
            password=DEFAULT_PASSWORD,
            roles={"socio": []},
            como_socio=True,
        )
        clase = self._crear_clase()
        reserva = self._crear_reserva(socio_duenio.persona_id, clase.clase_id)

        self.client.post(
            "/api/login",
            json={"email": socio_actor.email, "password": DEFAULT_PASSWORD},
        )

        response = self.client.post(
            "/api/asistencia/escanearQR",
            json={
                "dni": socio_duenio.dni,
                "id_reserva": reserva.reserva_id,
                "id_clase": clase.clase_id,
            },
        )

        db.session.refresh(reserva)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json["message"],
            "Como socio solo puedes escanear tus propios códigos QR de asistencia.",
        )
        self.assertEqual(reserva.estado, "confirmada")

    def test_socio_no_puede_generar_qr_de_otra_reserva(self):
        socio_actor = self._crear_persona(
            email="actor-qr@centro.test",
            dni="30000013",
            password=DEFAULT_PASSWORD,
            roles={"socio": []},
            como_socio=True,
        )
        socio_duenio = self._crear_persona(
            email="duenio-qr@centro.test",
            dni="30000014",
            password=DEFAULT_PASSWORD,
            roles={"socio": []},
            como_socio=True,
        )
        clase = self._crear_clase()
        reserva = self._crear_reserva(socio_duenio.persona_id, clase.clase_id)

        self.client.post(
            "/api/login",
            json={"email": socio_actor.email, "password": DEFAULT_PASSWORD},
        )

        response = self.client.post(f"/api/asistencia/generarQR/{reserva.reserva_id}")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json["message"],
            "Solo puedes generar el QR de tus propias reservas.",
        )

    def test_empleado_puede_escanear_qr_de_otro_socio(self):
        empleado = self._crear_persona(
            email="empleado@centro.test",
            dni="30000021",
            password=DEFAULT_PASSWORD,
            roles={"empleado": []},
            como_empleado=True,
        )
        socio_duenio = self._crear_persona(
            email="socio@centro.test",
            dni="30000022",
            password=DEFAULT_PASSWORD,
            roles={"socio": []},
            como_socio=True,
        )
        clase = self._crear_clase()
        reserva = self._crear_reserva(socio_duenio.persona_id, clase.clase_id)

        self.client.post(
            "/api/login",
            json={"email": empleado.email, "password": DEFAULT_PASSWORD},
        )

        response = self.client.post(
            "/api/asistencia/escanearQR",
            json={
                "dni": socio_duenio.dni,
                "id_reserva": reserva.reserva_id,
                "id_clase": clase.clase_id,
            },
        )

        db.session.refresh(reserva)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "success")
        self.assertEqual(reserva.estado, "asistio")

    def test_empleado_no_puede_escanear_qr_de_otra_clase(self):
        empleado = self._crear_persona(
            email="empleado-clase@centro.test",
            dni="30000023",
            password=DEFAULT_PASSWORD,
            roles={"empleado": []},
            como_empleado=True,
        )
        socio_duenio = self._crear_persona(
            email="socio-clase@centro.test",
            dni="30000024",
            password=DEFAULT_PASSWORD,
            roles={"socio": []},
            como_socio=True,
        )
        clase_seleccionada = self._crear_clase()
        otra_clase = self._crear_clase(horario_inicio=time(12, 0), horario_fin=time(13, 0))
        reserva = self._crear_reserva(socio_duenio.persona_id, otra_clase.clase_id)

        self.client.post(
            "/api/login",
            json={"email": empleado.email, "password": DEFAULT_PASSWORD},
        )

        response = self.client.post(
            "/api/asistencia/escanearQR",
            json={
                "dni": socio_duenio.dni,
                "id_reserva": reserva.reserva_id,
                "id_clase": clase_seleccionada.clase_id,
            },
        )

        db.session.refresh(reserva)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json["message"],
            "El QR escaneado no corresponde a la clase seleccionada.",
        )
        self.assertEqual(reserva.estado, "confirmada")

    def _crear_persona(self, email, dni, password, roles, como_socio=False, como_empleado=False):
        persona = Persona(
            dni=dni,
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

        for role_name in roles:
            role = Rol.query.filter_by(nombre=role_name).first()
            if role is None:
                role = Rol(nombre=role_name, descripcion=f"Rol {role_name}")
                db.session.add(role)
                db.session.flush()

            db.session.add(PersonaRolPuente(persona_id=persona.persona_id, rol_id=role.rol_id))

        db.session.commit()
        return persona

    def _crear_clase(self, horario_inicio=time(10, 0), horario_fin=time(11, 0)):
        profesor_index = Profesor.query.count() + 1
        profesor = Profesor(
            nombre=f"Profesor QR {profesor_index}",
            dni=f"9999{profesor_index:04d}",
            telefono=f"221500{profesor_index:04d}",
        )
        db.session.add(profesor)
        db.session.flush()

        clase = Clase(
            actividad=ActividadEnum.FUTBOL,
            fecha=date.today(),
            horario_inicio=horario_inicio,
            horario_fin=horario_fin,
            cancha="Cancha 1",
            nivel=NivelEnum.PRINCIPIANTE,
            cupos=12,
            tipo_clase=TipoClaseEnum.GRUPAL,
            profesor_id=profesor.profesor_id,
        )
        db.session.add(clase)
        db.session.commit()
        return clase

    def _crear_reserva(self, socio_id, clase_id):
        reserva = Reserva(
            clase_id=clase_id,
            socio_id=socio_id,
            tipo_reserva="estandar",
            estado="confirmada",
        )
        db.session.add(reserva)
        db.session.commit()
        return reserva
