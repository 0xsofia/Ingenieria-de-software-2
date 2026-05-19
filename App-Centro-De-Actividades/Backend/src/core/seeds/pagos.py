from datetime import datetime, timedelta

from src.core.database import db
from src.core.models.persona import Persona
from src.core.models.pago import Pago

PAYMENTS_TO_SEED = [
    {
        "external_ref": "seed-socio-01",
        "email": "socio@centro.test",
        "monto_bruto": "450.00",
        "descuento_pct": "0",
        "monto_pagado": "450.00",
        "estado": "aprobado",
        "fecha_pago": datetime.utcnow() - timedelta(days=12),
    },
    {
        "external_ref": "seed-socio-02",
        "email": "socio@centro.test",
        "monto_bruto": "380.00",
        "descuento_pct": "5",
        "monto_pagado": "361.00",
        "estado": "aprobado",
        "fecha_pago": datetime.utcnow() - timedelta(days=5),
    },
    {
        "external_ref": "seed-socio-03",
        "email": "socio@centro.test",
        "monto_bruto": "320.00",
        "descuento_pct": "0",
        "monto_pagado": None,
        "estado": "pendiente",
        "fecha_pago": None,
    },
]


def seed_pagos():
    persona = Persona.query.filter_by(email="socio@centro.test").first()
    if persona is None or persona.socio is None:
        return

    existing_refs = {
        pago.external_ref
        for pago in Pago.query.filter(Pago.external_ref.in_([item["external_ref"] for item in PAYMENTS_TO_SEED])).all()
    }

    for payment_data in PAYMENTS_TO_SEED:
        if payment_data["external_ref"] in existing_refs:
            continue

        pago = Pago(
            socio_id=persona.persona_id,
            reserva_id=None,
            abono_mensual_id=None,
            proveedor="mercadopago",
            external_ref=payment_data["external_ref"],
            monto_bruto=payment_data["monto_bruto"],
            descuento_pct=payment_data["descuento_pct"],
            monto_pagado=payment_data["monto_pagado"],
            estado=payment_data["estado"],
            fecha_pago=payment_data["fecha_pago"],
        )
        db.session.add(pago)

    db.session.commit()
