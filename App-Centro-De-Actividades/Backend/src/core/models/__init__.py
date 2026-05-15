# Import model modules here so Alembic autogenerate can see them.

from src.core.models.asistencia import (
    Actividad,
    AbonoMensual,
    Asistencia,
    Cancha,
    Clase,
    ListaEspera,
    Profesor,
    QrAsistencia,
    Reserva,
    Nivel,
)
from src.core.models.persona import (
    Empleado,
    Permiso,
    Persona,
    PersonaRolPuente,
    Rol,
    RolPermisoPuente,
    Socio,
)

__all__ = [
    "Persona",
    "Empleado",
    "Socio",
    "Rol",
    "Permiso",
    "PersonaRolPuente",
    "RolPermisoPuente",
    "Profesor",
    "Actividad",
    "Nivel",
    "Cancha",
    "Clase",
    "ListaEspera",
    "AbonoMensual",
    "Reserva",
    "QrAsistencia",
    "Asistencia",
]
