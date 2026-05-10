# Import model modules here so Alembic autogenerate can see them.

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
]
