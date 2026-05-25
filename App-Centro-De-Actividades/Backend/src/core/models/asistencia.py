from src.core.database import db
from datetime import datetime


class Asistencia(db.Model):
    __tablename__ = "asistencia"

    asistencia_id = db.Column(db.Integer, primary_key=True)
    reserva_id = db.Column(db.Integer, db.ForeignKey("reserva.reserva_id"), nullable=False, unique=True, index=True)
    qr_asistencia_id = db.Column(db.Integer, db.ForeignKey("qr_asistencia.qr_asistencia_id"), nullable=True, index=True)
    empleado_registro_id = db.Column(db.Integer, db.ForeignKey("empleado.persona_id"), nullable=True, index=True)
    fecha_hora = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    medio_registro = db.Column(db.String(50), nullable=False)

    reserva = db.relationship("Reserva", back_populates="asistencia")
    qr_asistencia = db.relationship("QrAsistencia", back_populates="asistencia")
