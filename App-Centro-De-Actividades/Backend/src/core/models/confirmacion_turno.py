from src.core.database import db


class ConfirmacionTurno(db.Model):
    __tablename__ = "confirmacion_turno"

    confirmacion_turno_id = db.Column(db.Integer, primary_key=True)

    lista_espera_id = db.Column(
        db.Integer,
        db.ForeignKey("lista_espera.lista_espera_id"),
        nullable=False,
        index=True,
    )
    socio_id = db.Column(
        db.Integer,
        db.ForeignKey("socio.persona_id"),
        nullable=False,
        index=True,
    )

    token = db.Column(db.String(32), unique=True, nullable=False, index=True)
    estado = db.Column(db.String(50), nullable=False, server_default="pendiente")

    creado_en = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
    )
    expira_en = db.Column(db.DateTime(timezone=True), nullable=False)
    confirmado_en = db.Column(db.DateTime(timezone=True), nullable=True)
