from src.core.database import db
from datetime import date, time
 

class Profesor(db.Model):
    __tablename__ = "profesor"

    profesor_id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    dni = db.Column(db.String(20), nullable=False, unique=True) #luego reveer si es el tipo conveniente para el dni
    telefono = db.Column(db.String(25), nullable=False)
    is_eliminated = db.Column(db.Boolean, nullable=False, server_default=db.text('false'))
    creado_en = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    
    clases = db.relationship(
        "Clase",
        back_populates="profesor")