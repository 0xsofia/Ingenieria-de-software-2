# Import model modules here so Alembic autogenerate can see them.

from src.core.models.abono_mensual import AbonoMensual
from src.core.models.actividad import Actividad
from src.core.models.clase import Clase
from src.core.models.credito import Credito
from src.core.models.lista_espera import ListaEspera
from src.core.models.pago import Pago
from src.core.models.persona import (
    Empleado,
    Permiso,
    Persona,
    PersonaRolPuente,
    Rol,
    RolPermisoPuente,
    Socio,
)
from src.core.models.reserva import Reserva

__all__ = [
    "Actividad",
    "Clase",
    "ListaEspera",
    "AbonoMensual",
    "Reserva",
    "Pago",
    "Credito",
    "Persona",
    "Empleado",
    "Socio",
    "Rol",
    "Permiso",
    "PersonaRolPuente",
    "RolPermisoPuente",
]
