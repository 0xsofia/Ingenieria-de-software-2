from src.core.database import db


class Reserva(db.Model):
    __tablename__ = "reserva"
    __table_args__ = (
        db.Index(
            "uq_reserva_clase_socio_activa",
            "clase_id",
            "socio_id",
            unique=True,
            postgresql_where=db.text("estado IN ('pendiente_pago', 'confirmada')"),
        ),
    )

    reserva_id = db.Column(db.Integer, primary_key=True)

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

    abono_mensual_id = db.Column(
        db.Integer,
        db.ForeignKey("abono_mensual.abono_mensual_id"),
        nullable=True,
        index=True,
    )
    lista_espera_origen_id = db.Column(
        db.Integer,
        db.ForeignKey("lista_espera.lista_espera_id"),
        nullable=True,
        index=True,
    )

    tipo_reserva = db.Column(db.String(50), nullable=False)
    estado = db.Column(db.String(50), nullable=False, server_default="pendiente")

    creada_en = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
    )
    confirmada_en = db.Column(db.DateTime(timezone=True), nullable=True)
    cancelada_en = db.Column(db.DateTime(timezone=True), nullable=True)

    clase = db.relationship("Clase", back_populates="reservas")
    asistencia = db.relationship("Asistencia", back_populates="reserva", uselist=False, cascade="all, delete-orphan")
    qr_asistencias = db.relationship("QrAsistencia", back_populates="reserva", cascade="all, delete-orphan")
