from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.core.database import db
from src.core.enums.clase_enum import ActividadEnum, NivelEnum, TipoClaseEnum
from src.core.models.clase import Clase
from src.core.models.profesor import Profesor

CLASE_RESERVADA_TEMPLATE = {
    "actividad": "Voley",
    "cancha": "Voley",
    "nivel": "Principiante",
    "cupos": 1,
    "profesor_dni": "12345678",
    "precio": 500,
}

CLASES_BASE_TEMPLATE = [
    {
        "actividad": "Voley",
        "cancha": "Voley",
        "nivel": "Principiante",
        "cupos": 8,
        "profesor_dni": "12345678",
        "precio": 500,
    },
    {
        "actividad": "Futbol",
        "cancha": "Cancha B",
        "nivel": "Intermedio",
        "cupos": 10,
        "profesor_dni": "87654321",
        "precio": 500,
    },
    {
        "actividad": "Basquet",
        "cancha": "Cancha D",
        "nivel": "Intermedio",
        "cupos": 12,
        "profesor_dni": "11223344",
        "precio": 500,
    },
    {
        "actividad": "Futbol",
        "cancha": "Cancha A",
        "nivel": "Avanzado",
        "cupos": 6,
        "profesor_dni": "44332211",
        "precio": 500,
    },
]

CLASES_OFFSET_MINUTES = (0, 15, 30, 60)
SEED_TIMEZONE = ZoneInfo("America/Argentina/Buenos_Aires")


def seed_clases(seed_datetime=None):
    for clase_data in _build_dynamic_clases_to_seed(seed_datetime):
        _get_or_create_clase(clase_data)

    db.session.commit()


def get_seed_reference_datetime(seed_datetime=None):
    if seed_datetime is None:
        return datetime.now(SEED_TIMEZONE)

    if seed_datetime.tzinfo is None:
        return seed_datetime.replace(tzinfo=SEED_TIMEZONE)

    return seed_datetime.astimezone(SEED_TIMEZONE)


def _build_dynamic_clases_to_seed(seed_datetime=None):
    seed_datetime = get_seed_reference_datetime(seed_datetime)
    base_datetime = seed_datetime.replace(minute=0, second=0, microsecond=0)
    clase_reservada_datetime = base_datetime - timedelta(hours=1)
    clases_to_seed = [
        {
            **CLASE_RESERVADA_TEMPLATE,
            "fecha": clase_reservada_datetime.strftime("%Y-%m-%d"),
            "horario_inicio": clase_reservada_datetime.strftime("%H:%M"),
        }
    ]

    for clase_template, offset_minutes in zip(
        CLASES_BASE_TEMPLATE, CLASES_OFFSET_MINUTES
    ):
        clase_datetime = base_datetime + timedelta(minutes=offset_minutes)
        clases_to_seed.append(
            {
                **clase_template,
                "fecha": clase_datetime.strftime("%Y-%m-%d"),
                "horario_inicio": clase_datetime.strftime("%H:%M"),
            }
        )

    return clases_to_seed


def _get_or_create_clase(clase_data):
    profesor = Profesor.query.filter_by(dni=clase_data["profesor_dni"]).first()
    if profesor is None:
        return

    fecha_obj = datetime.strptime(clase_data["fecha"], "%Y-%m-%d").date()
    horario_inicio_obj = datetime.strptime(clase_data["horario_inicio"], "%H:%M").time()

    clase = Clase.query.filter_by(
        profesor_id=profesor.profesor_id,
        fecha=fecha_obj,
        horario_inicio=horario_inicio_obj,
        actividad=ActividadEnum(clase_data["actividad"]),
    ).first()

    tipo_clase = (
        TipoClaseEnum.PARTICULAR if clase_data["cupos"] == 1 else TipoClaseEnum.GRUPAL
    )

    if clase is None:
        clase = Clase(
            actividad=ActividadEnum(clase_data["actividad"]),
            fecha=fecha_obj,
            horario_inicio=horario_inicio_obj,
            horario_fin=(
                datetime.combine(fecha_obj, horario_inicio_obj) + timedelta(hours=1)
            ).time(),
            cancha=clase_data["cancha"],
            nivel=NivelEnum(clase_data["nivel"]),
            cupos=clase_data["cupos"],
            precio=clase_data.get("precio"),
            tipo_clase=tipo_clase,
            profesor_id=profesor.profesor_id,
        )
        db.session.add(clase)
        db.session.flush()
        return clase

    clase.cancha = clase_data["cancha"]
    clase.nivel = NivelEnum(clase_data["nivel"])
    clase.cupos = clase_data["cupos"]
    clase.precio = clase_data.get("precio")
    clase.tipo_clase = tipo_clase
    clase.horario_fin = (
        datetime.combine(fecha_obj, horario_inicio_obj) + timedelta(hours=1)
    ).time()
    db.session.flush()
    return clase
