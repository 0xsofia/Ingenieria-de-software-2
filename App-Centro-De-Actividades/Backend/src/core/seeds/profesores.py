from src.core.database import db
from src.core.models.profesor import Profesor


PROFESORES_TO_SEED = [
    {
        "nombre": "Juan García",
        "dni": "12345678",
        "telefono": "1234567890",
    },
    {
        "nombre": "María López",
        "dni": "87654321",
        "telefono": "0987654321",
    },
    {
        "nombre": "Carlos Martínez",
        "dni": "11223344",
        "telefono": "5555555555",
    },
    {
        "nombre": "Ana Rodríguez",
        "dni": "44332211",
        "telefono": "6666666666",
    },
]


def seed_profesores():
    for profesor_data in PROFESORES_TO_SEED:
        _get_or_create_profesor(profesor_data)
    
    db.session.commit()


def _get_or_create_profesor(profesor_data):
    dni = profesor_data["dni"].strip()
    profesor = Profesor.query.filter_by(dni=dni).first()

    if profesor is None:
        profesor = Profesor(
            nombre=profesor_data["nombre"],
            dni=dni,
            telefono=profesor_data["telefono"],
        )
        db.session.add(profesor)
        db.session.flush()
        return profesor

    # Si existe, actualiza los datos
    profesor.nombre = profesor_data["nombre"]
    profesor.telefono = profesor_data["telefono"]
    db.session.flush()
    return profesor
