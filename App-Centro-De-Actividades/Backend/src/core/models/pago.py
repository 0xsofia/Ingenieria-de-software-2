from src.core.database import db


class Pago(db.Model):
    __tablename__ = "pago"

    pago_id = db.Column(db.Integer, primary_key=True)

    socio = db.relationship("Socio", backref="pagos")
    
    socio_id = db.Column(
        db.Integer,
        db.ForeignKey("socio.persona_id"),
        nullable=False,
        index=True,
    )
    reserva_id = db.Column(
        db.Integer,
        db.ForeignKey("reserva.reserva_id"),
        nullable=True,
        index=True,
    )
    abono_mensual_id = db.Column(
        db.Integer,
        db.ForeignKey("abono_mensual.abono_mensual_id"),
        nullable=True,
        index=True,
    )

    proveedor = db.Column(db.String(50), nullable=False, server_default="mercadopago")
    external_ref = db.Column(db.String(255), nullable=True, index=True)

    monto_bruto = db.Column(db.Numeric(10, 2), nullable=False)
    descuento_pct = db.Column(db.Numeric(5, 2), nullable=False, server_default="0")
    monto_pagado = db.Column(db.Numeric(10, 2), nullable=True)

    estado = db.Column(db.String(50), nullable=False, server_default="pendiente")
    fecha_pago = db.Column(db.DateTime(timezone=True), nullable=True)
