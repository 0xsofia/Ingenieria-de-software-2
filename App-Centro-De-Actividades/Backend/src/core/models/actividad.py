from src.core.database import db


class Actividad(db.Model):
    __tablename__ = "actividad"

    actividad_id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), unique=True, nullable=False, index=True)
