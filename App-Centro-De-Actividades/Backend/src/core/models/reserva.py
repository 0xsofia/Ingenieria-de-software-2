from src.core.database import db

class Reserva(db.Model):
    __tablename__ = "reserva"

    id = db.Column(db.Integer, primary_key=True)
    dni_cliente = db.Column(db.String(20), nullable=False)
    clase_id = db.Column(db.Integer, db.ForeignKey('clase.id'))
    asistencia = db.Column(db.Boolean, default=False)