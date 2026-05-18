from src.core.models.actividad import Actividad
from src.core.database import db

ACTIVIDADES_SEED = [
    {"nombre": "Futbol"},
    {"nombre": "Voley"},
    {"nombre": "Basquet"},
    {"nombre": "Padel"},
]


def seed_actividades():
    for actividad_data in ACTIVIDADES_SEED:
        nombre = actividad_data["nombre"].strip()
        actividad = Actividad.query.filter_by(nombre=nombre).first()

        if actividad is None:
            actividad = Actividad(nombre=nombre)
            db.session.add(actividad)
        else:
            actividad.nombre = nombre

    db.session.commit()
