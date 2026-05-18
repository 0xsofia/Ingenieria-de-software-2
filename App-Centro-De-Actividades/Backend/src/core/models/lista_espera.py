from src.core.database import db


class ListaEspera(db.Model):
    __tablename__ = "lista_espera"

    lista_espera_id = db.Column(db.Integer, primary_key=True)

    clase_id = db.Column(
        db.Integer,
        db.ForeignKey("clase.clase_id"),
        nullable=False,
        index=True,
    )
    socio_id = db.Column(
        db.Integer,
        db.ForeignKey("socio.persona_id"),
        nullable=False,
        index=True,
    )

    posicion = db.Column(db.Integer, nullable=False)
    estado = db.Column(db.String(50), nullable=False, server_default="pendiente")

    creada_en = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
    )

    notificado_en = db.Column(db.DateTime(timezone=True), nullable=True)
    vence_confirmacion_en = db.Column(db.DateTime(timezone=True), nullable=True)
    confirmada_en = db.Column(db.DateTime(timezone=True), nullable=True)
