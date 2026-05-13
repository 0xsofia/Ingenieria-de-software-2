from src.core.database import db
from src.core.models import Clase, TipoClaseEnum
from datetime import timedelta, datetime

class ClaseService:

    @staticmethod
    def crear_clase(data):

        clase_existente = Clase.query.filter_by(
            profesor_id=data["profesor_id"],
            fecha=data["fecha"],
            horario_inicio=data["horario_inicio"],
            actividad=data["actividad"]
        ).first()

        if clase_existente:
            raise Exception("El profesor ya tiene una clase registrada en ese horario")

        horario_inicio = datetime.combine(
            data["fecha"],
            data["horario_inicio"]
        )

        horario_fin = (
            horario_inicio + timedelta(hours=1)
        ).time()

        tipo_clase = TipoClaseEnum.PARTICULAR if data["cupo"] == 1 else TipoClaseEnum.GRUPAL

        nueva_clase = Clase(
            profesor_id=data["profesor_id"],
            fecha=data["fecha"],
            horario_inicio=data["horario_inicio"],
            horario_fin=horario_fin,
            actividad=data["actividad"],
            cancha=data["cancha"],
            nivel=data["nivel"],
            cupos=data["cupos"],
            tipo_clase=tipo_clase
        )

        db.session.add(nueva_clase)
        db.session.commit()

        return nueva_clase