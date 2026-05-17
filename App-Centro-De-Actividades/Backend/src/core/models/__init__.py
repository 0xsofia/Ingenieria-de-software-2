# Import model modules here so Alembic autogenerate can see them.
from src.core.models.actividad import Actividad
from src.core.models.clase import (Clase,TipoClaseEnum)
from src.core.models.profesor import Profesor
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
    "Actividad",
    "Clase",
    "Profesor",
]
