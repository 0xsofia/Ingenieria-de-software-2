from datetime import datetime, timedelta

from src.core.database import db
from src.core.enums.clase_enum import ActividadEnum, NivelEnum, TipoClaseEnum
from src.core.models.clase import Clase
from src.core.models.profesor import Profesor

CLASES_TO_SEED = [
    {
        "actividad": "Voley",
        "fecha": "2026-06-01",
        "horario_inicio": "08:00",
        "cancha": "Voley",
        "nivel": "Principiante",
        "cupos": 8,
        "profesor_dni": "12345678",
        "precio": 500,
    },
    {
        "actividad": "Futbol",
        "fecha": "2026-06-01",
        "horario_inicio": "18:00",
        "cancha": "Cancha B",
        "nivel": "Intermedio",
        "cupos": 10,
        "profesor_dni": "87654321",
        "precio": 500,
    },
    {
        "actividad": "Basquet",
        "fecha": "2026-06-12",
        "horario_inicio": "18:00",
        "cancha": "Cancha D",
        "nivel": "Intermedio",
        "cupos": 12,
        "profesor_dni": "44332211",
        "precio": 500,
    },
    {
        "actividad": "Voley",
        "fecha": "2026-05-20",
        "horario_inicio": "01:00",
        "cancha": "Voley",
        "nivel": "Principiante",
        "cupos": 10,
        "profesor_dni": "12345678",
    },
    {
        "actividad": "Futbol",
        "fecha": "2026-05-20",
        "horario_inicio": "01:00",
        "cancha": "Voley",
        "nivel": "Principiante",
        "cupos": 10,
        "profesor_dni": "12345678",
    },
]


def seed_clases():
    for clase_data in CLASES_TO_SEED:
        _get_or_create_clase(clase_data)

    db.session.commit()


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
