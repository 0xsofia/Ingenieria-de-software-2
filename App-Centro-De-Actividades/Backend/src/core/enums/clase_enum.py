from enum import Enum

class ActividadEnum(Enum):
    VOLEY = "Voley"
    FUTBOL = "Futbol"
    PADEL = "Padel"
    BASQUET = "Basquet"


class NivelEnum(Enum):
    PRINCIPIANTE = "Principiante"
    INTERMEDIO = "Intermedio"
    AVANZADO = "Avanzado"


class TipoClaseEnum(Enum):
    GRUPAL = "Grupal"
    PARTICULAR = "Particular"