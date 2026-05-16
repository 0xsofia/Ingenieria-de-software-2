from src.core.enums.clase_enum import ActividadEnum, NivelEnum, TipoClaseEnum
from datetime import date, time
 

class Clase(db.Model):
    __tablename__ = "clase"

    clase_id = db.Column(db.Integer, primary_key=True)
    actividad = db.Column(db.Enum(ActividadEnum), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    horario_inicio = db.Column(db.Time, nullable=False)
    horario_fin = db.Column(db.Time, nullable=False)
    cancha = db.Column(db.String(100), nullable=False)
    nivel = db.Column(db.Enum(NivelEnum),nullable=False)
    cupos = db.Column(db.Integer, nullable=False)#ver de ponerle por defualt 0 o mayor que cero como regla aca?
    tipo_clase = db.Column(db.Enum(TipoClaseEnum),nullable=False)
    creado_en = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())

    profesor_id = db.Column(
        db.Integer,
        db.ForeignKey("profesor.profesor_id"),
        nullable=False
    )

    profesor = db.relationship("Profesor", back_populates="clases")
