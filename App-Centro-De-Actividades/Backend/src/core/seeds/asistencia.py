from datetime import date, datetime, timedelta, time

from src.core.database import db
from src.core.models.persona import Empleado, Persona, Socio
from src.core.models.asistencia import (
    Actividad,
    Cancha,
    Clase,
    Profesor,
    QrAsistencia,
    Reserva,
    Nivel,
    Asistencia,
)


def seed_asistencia():
    socio = _get_socio_by_email("socio@centro.test")
    empleado = _get_empleado_by_email("empleado@centro.test")

    if socio is None or empleado is None:
        return

    actividad = _get_or_create_actividad("Yoga")
    nivel = _get_or_create_nivel("Intermedio")
    cancha = _get_or_create_cancha("Sala Principal")
    profesor = _get_or_create_profesor("70000001", "Profesor Asistencia")
    clase = _get_or_create_clase(actividad, nivel, profesor, cancha)

    reserva_abierta = _get_or_create_reserva(
        clase,
        socio,
        tipo_reserva="normal",
        estado="confirmada",
        confirmada_en=datetime.utcnow(),
    )

    _get_or_create_qr_asistencia(
        reserva_abierta,
        token_hash="QR-ASISTENCIA-001",
        expira_en=datetime.utcnow() + timedelta(hours=3),
    )

    reserva_asistida = _get_or_create_reserva(
        clase,
        socio,
        tipo_reserva="normal",
        estado="asistida",
        confirmada_en=datetime.utcnow() - timedelta(days=1),
        unique_suffix="-attended",
    )

    qr_asistida = _get_or_create_qr_asistencia(
        reserva_asistida,
        token_hash="QR-ASISTENCIA-USED-001",
        expira_en=datetime.utcnow() - timedelta(hours=1),
        escaneado_en=datetime.utcnow() - timedelta(hours=1),
        estado="usado",
    )

    _get_or_create_asistencia(
        reserva_asistida,
        qr_asistida,
        empleado,
        fecha_hora=datetime.utcnow() - timedelta(hours=1),
        medio_registro="qr",
    )

    db.session.commit()


def _get_socio_by_email(email):
    return Socio.query.join(Persona).filter(Persona.email == email.strip().lower()).first()


def _get_empleado_by_email(email):
    return Empleado.query.join(Persona).filter(Persona.email == email.strip().lower()).first()


def _get_or_create_profesor(dni, nombre):
    profesor = Profesor.query.filter_by(dni=dni).first()
    if profesor is None:
        profesor = Profesor(dni=dni, nombre=nombre)
        db.session.add(profesor)
        db.session.flush()
    return profesor


def _get_or_create_actividad(nombre):
    actividad = Actividad.query.filter_by(nombre=nombre).first()
    if actividad is None:
        actividad = Actividad(nombre=nombre)
        db.session.add(actividad)
        db.session.flush()
    return actividad


def _get_or_create_nivel(nombre):
    nivel = Nivel.query.filter_by(nombre=nombre).first()
    if nivel is None:
        nivel = Nivel(nombre=nombre)
        db.session.add(nivel)
        db.session.flush()
    return nivel


def _get_or_create_cancha(nombre):
    cancha = Cancha.query.filter_by(nombre=nombre).first()
    if cancha is None:
        cancha = Cancha(nombre=nombre)
        db.session.add(cancha)
        db.session.flush()
    return cancha


def _get_or_create_clase(actividad, nivel, profesor, cancha):
    clase = Clase.query.filter_by(
        actividad_id=actividad.actividad_id,
        nivel_id=nivel.nivel_id,
        profesor_id=profesor.profesor_id,
        cancha_id=cancha.cancha_id,
    ).first()

    if clase is None:
        clase = Clase(
            actividad_id=actividad.actividad_id,
            nivel_id=nivel.nivel_id,
            profesor_id=profesor.profesor_id,
            cancha_id=cancha.cancha_id,
            fecha_clase=date.today() + timedelta(days=1),
            hora_inicio=time(hour=18, minute=0),
            hora_fin=time(hour=19, minute=0),
            cupo_total=20,
            precio=1500,
            estado="activa",
        )
        db.session.add(clase)
        db.session.flush()
    return clase


def _get_or_create_reserva(
    clase,
    socio,
    tipo_reserva="normal",
    estado="confirmada",
    confirmada_en=None,
    unique_suffix="",
):
    query = Reserva.query.filter_by(
        clase_id=clase.clase_id,
        socio_id=socio.persona_id,
        tipo_reserva=tipo_reserva,
    )

    if unique_suffix:
        query = query.filter(Reserva.estado == estado)

    reserva = query.first()
    if reserva is None:
        reserva = Reserva(
            clase_id=clase.clase_id,
            socio_id=socio.persona_id,
            tipo_reserva=tipo_reserva,
            estado=estado,
            creada_en=datetime.utcnow(),
            confirmada_en=confirmada_en,
        )
        db.session.add(reserva)
        db.session.flush()
    return reserva


def _get_or_create_qr_asistencia(
    reserva,
    token_hash,
    expira_en,
    escaneado_en=None,
    estado="activo",
):
    qr = QrAsistencia.query.filter_by(token_hash=token_hash).first()
    if qr is None:
        qr = QrAsistencia(
            reserva_id=reserva.reserva_id,
            token_hash=token_hash,
            generado_en=datetime.utcnow(),
            expira_en=expira_en,
            escaneado_en=escaneado_en,
            estado=estado,
        )
        db.session.add(qr)
        db.session.flush()
    return qr


def _get_or_create_asistencia(reserva, qr_asistencia, empleado, fecha_hora, medio_registro):
    asistencia = Asistencia.query.filter_by(reserva_id=reserva.reserva_id).first()
    if asistencia is None:
        asistencia = Asistencia(
            reserva_id=reserva.reserva_id,
            qr_asistencia_id=qr_asistencia.qr_asistencia_id,
            empleado_registro_id=empleado.persona_id,
            fecha_hora=fecha_hora,
            medio_registro=medio_registro,
        )
        db.session.add(asistencia)
        db.session.flush()
    return asistencia
