# Import model modules here so Alembic autogenerate can see them.

from src.core.models.abono_mensual import AbonoMensual
from src.core.models.credito import Credito
from src.core.models.lista_espera import ListaEspera
from src.core.models.pago import Pago
from src.core.models.actividad import Actividad
from src.core.models.clase import Clase, TipoClaseEnum
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
from src.core.models.reserva import Reserva
from src.core.models.asistencia import Asistencia
from src.core.models.qr_asistencia import QrAsistencia

__all__ = [
    "ListaEspera",
    "AbonoMensual",
    "Reserva",
    "Asistencia",
    "QrAsistencia",
    "Pago",
    "Credito",
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
