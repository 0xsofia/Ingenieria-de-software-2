from src.core.database import db
from src.core.models.profesor import Profesor


PROFESORES_TO_SEED = [
    {
        "nombre": "Carlos",
        "dni": "12345678",
        "telefono": "2215003101",
    },
    {
        "nombre": "Maria Lopez",
        "dni": "87654321",
        "telefono": "2215003102",
    },
    {
        "nombre": "Juan Garcia",
        "dni": "11223344",
        "telefono": "2215003103",
    },
    {
        "nombre": "Ana Rodriguez",
        "dni": "44332211",
        "telefono": "2215003104",
    },
    {
        "nombre": "Sofia Martinez",
        "dni": "44620873",
        "telefono": "2215003105",
    },
    {
        "nombre": "Profesor Sin Clases Futuras",
        "dni": "55779911",
        "telefono": "2215003106",
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

    profesor.nombre = profesor_data["nombre"]
    profesor.telefono = profesor_data["telefono"]
    db.session.flush()
    return profesor
