from datetime import date, time, timedelta

import random
from src.core.database import db
from src.core.models.actividad import Actividad
from src.core.models.clase import Clase


def seed_clases():
    """Seed mínimo para soportar la HU de reserva espontánea."""

    target_date = _random_day_this_week(date.today())  # 0=Lun, 1=Mar

    basquet = _get_or_create_actividad("básquet")
    tenis = _get_or_create_actividad("tenis")

    _get_or_create_clase(
        actividad_id=basquet.actividad_id,
        fecha_clase=target_date,
        hora_inicio=time(18, 0),
        hora_fin=time(19, 0),
        cupo_total=10,
        precio=1000,
    )

    _get_or_create_clase(
        actividad_id=tenis.actividad_id,
        fecha_clase=target_date,
        hora_inicio=time(17, 0),
        hora_fin=time(18, 0),
        cupo_total=0,
        precio=1000,
    )

    db.session.commit()


def _get_or_create_actividad(nombre):
    actividad = Actividad.query.filter(db.func.lower(Actividad.nombre) == nombre.lower()).first()

    if actividad is None:
        actividad = Actividad(nombre=nombre)
        db.session.add(actividad)
        db.session.flush()

    return actividad


def _get_or_create_clase(
    actividad_id,
    fecha_clase,
    hora_inicio,
    hora_fin,
    cupo_total,
    precio,
):
    clase = (
        Clase.query.filter_by(
            actividad_id=actividad_id,
            fecha_clase=fecha_clase,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
        ).first()
    )

    if clase is None:
        clase = Clase(
            actividad_id=actividad_id,
            fecha_clase=fecha_clase,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            cupo_total=cupo_total,
            precio=precio,
            estado="activa",
        )
        db.session.add(clase)

    return clase


def _next_weekday(start, weekday):
    days_ahead = (weekday - start.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return start + timedelta(days=days_ahead)

def _random_day_this_week(start):
    today = start
    end_of_week = today + timedelta(days=(6 - today.weekday()))
    random_day = today + timedelta(days=random.randint(0, (end_of_week - today).days))
    return random_day