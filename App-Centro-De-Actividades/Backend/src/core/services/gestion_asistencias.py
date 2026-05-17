import jwt
import os
from datetime import datetime, timedelta
from ...core.models import db, reserva, clase

class AsistenciaService:
     def __init__(self, reserva):
        self.reserva = reserva

def generar_token_asistencia(reserva_id):
    reserva = reserva.Reserva.query.get_or_404(reserva_id)
    clase = clase.Clase.query.get(reserva.clase_id)
    ahora = datetime.now()

    if abs((clase.horario_inicio - ahora).total_seconds()) > 900:
        raise ValueError("Fuera de rango horario para generar QR")

    return jwt.encode({
        "reserva_id": reserva.id,
        "exp": ahora + timedelta(minutes=15)
    }, os.getenv("SECRET_KEY"), algorithm="HS256")

@staticmethod
def registrar_asistencia_qr(token):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
        reserva = reserva.query.get(payload['reserva_id'])

        if not reserva:
            raise Exception("Reserva no encontrada")
        if reserva.asistencia:
            raise ValueError("La asistencia ya fue registrada") # Escenario 4 [cite: 260]

        reserva.asistencia = True
        db.session.commit()
        return "Asistencia registrada exitosamente"
    except jwt.ExpiredSignatureError:
        raise ValueError("El QR ha expirado")
    except jwt.InvalidTokenError:
        raise ValueError("QR inválido") # Escenario 3 [cite: 260]