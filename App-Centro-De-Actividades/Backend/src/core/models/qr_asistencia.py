from src.core.database import db
from datetime import datetime


class QrAsistencia(db.Model):
    __tablename__ = "qr_asistencia"

    qr_asistencia_id = db.Column(db.Integer, primary_key=True)
    reserva_id = db.Column(db.Integer, db.ForeignKey("reserva.reserva_id"), nullable=False, index=True)
    token_hash = db.Column(db.String(255), unique=True, nullable=False, index=True)
    generado_en = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    expira_en = db.Column(db.DateTime(timezone=True), nullable=True)
    escaneado_en = db.Column(db.DateTime(timezone=True), nullable=True)
    estado = db.Column(db.String(50), nullable=False, server_default="activo")

    reserva = db.relationship("Reserva", back_populates="qr_asistencias")
    asistencia = db.relationship("Asistencia", back_populates="qr_asistencia", uselist=False)

    def mark_scanned(self):
        self.escaneado_en = datetime.utcnow()
        self.estado = "escaneado"
