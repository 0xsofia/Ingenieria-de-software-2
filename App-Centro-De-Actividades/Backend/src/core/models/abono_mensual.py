from src.core.database import db


class AbonoMensual(db.Model):
    __tablename__ = "abono_mensual"

    abono_mensual_id = db.Column(db.Integer, primary_key=True)

    socio_id = db.Column(
        db.Integer,
        db.ForeignKey("socio.persona_id"),
        nullable=False,
        index=True,
    )
    actividad_id = db.Column(
        db.Integer,
        db.ForeignKey("actividad.actividad_id"),
        nullable=False,
        index=True,
    )

    abono_anterior_id = db.Column(db.Integer, nullable=True, index=True)

    periodo_inicio = db.Column(db.Date, nullable=False)
    periodo_fin = db.Column(db.Date, nullable=False)

    hora_inicio = db.Column(db.Time, nullable=False)
    dia_semana = db.Column(db.String(20), nullable=False)

    descuento_aplicado_pct = db.Column(db.Numeric(5, 2), nullable=False, server_default="0")
    prioridad_renovacion = db.Column(db.Boolean, nullable=False, server_default=db.false())
    fecha_limite_renovacion = db.Column(db.Date, nullable=True)

    estado = db.Column(db.String(50), nullable=False, server_default="activo")
    creado_en = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
    )
