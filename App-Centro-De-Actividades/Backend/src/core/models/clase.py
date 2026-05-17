from src.core.database import db


class Clase(db.Model):
    __tablename__ = "clase"

    clase_id = db.Column(db.Integer, primary_key=True)

    actividad_id = db.Column(
        db.Integer,
        db.ForeignKey("actividad.actividad_id"),
        nullable=False,
        index=True,
    )

    nivel_id = db.Column(db.Integer, nullable=True, index=True)
    profesor_id = db.Column(db.Integer, nullable=True, index=True)
    cancha_id = db.Column(db.Integer, nullable=True, index=True)

    fecha_clase = db.Column(db.Date, nullable=False, index=True)
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fin = db.Column(db.Time, nullable=False)

    cupo_total = db.Column(db.Integer, nullable=False)
    precio = db.Column(db.Numeric(10, 2), nullable=False)

    estado = db.Column(db.String(50), nullable=False, server_default="activa")
    cancelada_en = db.Column(db.DateTime(timezone=True), nullable=True)

    actividad = db.relationship("Actividad")
