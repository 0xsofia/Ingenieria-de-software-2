from src.core.models.actividad import Actividad


class ActividadService:
    @staticmethod
    def obtener_actividades():
        return Actividad.query.order_by(Actividad.nombre).all()
