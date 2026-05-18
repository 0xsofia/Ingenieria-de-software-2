from src.core.database import db


class Credito(db.Model):
    __tablename__ = "credito"

    credito_id = db.Column(db.Integer, primary_key=True)

    socio_id = db.Column(
        db.Integer,
        db.ForeignKey("socio.persona_id"),
        nullable=False,
        index=True,
    )

    cancelacion_reserva_origen_id = db.Column(db.Integer, nullable=True, index=True)
    clase_cancelada_origen_id = db.Column(db.Integer, nullable=True, index=True)

    reserva_que_consume_id = db.Column(
        db.Integer,
        db.ForeignKey("reserva.reserva_id"),
        nullable=True,
        unique=True,
    )

    otorgado_en = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
    )
    consumido_en = db.Column(db.DateTime(timezone=True), nullable=True)

    estado = db.Column(db.String(50), nullable=False, server_default="disponible")
