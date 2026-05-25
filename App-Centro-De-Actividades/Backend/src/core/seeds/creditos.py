from src.core.database import db
from src.core.models.credito import Credito
from src.core.models.persona import Persona

CREDITOS_TO_SEED = [
    {
        "email": "credito@gmail.com",
        "cantidad": 2,
    },
]


def seed_creditos():
    for credito_data in CREDITOS_TO_SEED:
        email = credito_data["email"].strip().lower()
        persona = Persona.query.filter_by(email=email).first()
        if persona is None or persona.socio is None:
            continue

        socio_id = persona.socio.persona_id
        existentes = (
            Credito.query.filter_by(socio_id=socio_id)
            .filter(Credito.reserva_que_consume_id.is_(None))
            .filter(Credito.consumido_en.is_(None))
            .filter(db.func.lower(Credito.estado) == "disponible")
            .count()
        )

        objetivo = int(credito_data.get("cantidad", 1))
        for _ in range(max(objetivo - existentes, 0)):
            credito = Credito(
                socio_id=socio_id,
                estado="disponible",
            )
            db.session.add(credito)

    db.session.commit()
