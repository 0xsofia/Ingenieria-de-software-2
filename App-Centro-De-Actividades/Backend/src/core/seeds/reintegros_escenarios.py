from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid

from src.core.bcrypt_and_session import bcrypt
from src.core.database import db
from src.core.models.clase import Clase
from src.core.models.pago import Pago
from src.core.models.persona import Persona, PersonaRolPuente, Rol, Socio
from src.core.models.reserva import Reserva

DEFAULT_PASSWORD = "123456."


def seed_reintegros_escenarios(seed_datetime=None):
    """Crea datos semilla para probar los 4 escenarios de reintegro.

    Escenarios (ver src.core.services.reservas.cancelar_reserva_espontanea):
      - escenario_1: reintegro_aplica=True,  sancion_aplicada=False
      - escenario_2: reintegro_aplica=False, sancion_aplicada=False
      - escenario_3: reintegro_aplica=True,  sancion_aplicada=True
      - escenario_4: reintegro_aplica=False, sancion_aplicada=True

    Nota: Para escenario_3/4 se precargan 3 cancelaciones en el mes.
    """

    now = datetime.now(timezone.utc)
    target_classes = _resolve_target_classes(now)
    if target_classes is None:
        print("⚠️  [SEED] No hay clases base suficientes; se omiten seeds de reintegros.")
        return

    rol_socio = _get_or_create_role("socio")

    cases = [
        {
            "scenario": "escenario_1",
            "email": "reintegro1@centro.test",
            "dni": "39900001",
            "nombre": "Reintegro",
            "apellido": "Escenario1",
            "target_reserva_id": 9101,
            "target_clase": target_classes["refund"],
            "needs_sancion": False,
        },
        {
            "scenario": "escenario_2",
            "email": "reintegro2@centro.test",
            "dni": "39900002",
            "nombre": "Reintegro",
            "apellido": "Escenario2",
            "target_reserva_id": 9102,
            "target_clase": target_classes["no_refund"],
            "needs_sancion": False,
        },
        {
            "scenario": "escenario_3",
            "email": "reintegro3@centro.test",
            "dni": "39900003",
            "nombre": "Reintegro",
            "apellido": "Escenario3",
            "target_reserva_id": 9103,
            "target_clase": target_classes["refund"],
            "needs_sancion": True,
            "cancelled_base_id": 9200,
        },
        {
            "scenario": "escenario_4",
            "email": "reintegro4@centro.test",
            "dni": "39900004",
            "nombre": "Reintegro",
            "apellido": "Escenario4",
            "target_reserva_id": 9104,
            "target_clase": target_classes["no_refund"],
            "needs_sancion": True,
            "cancelled_base_id": 9300,
        },
    ]

    for case in cases:
        socio_id = _ensure_socio_user(
            email=case["email"],
            dni=case["dni"],
            nombre=case["nombre"],
            apellido=case["apellido"],
            rol=rol_socio,
        )

        if case.get("needs_sancion"):
            _ensure_cancelled_reservas_in_month(
                socio_id=socio_id,
                base_reserva_id=int(case["cancelled_base_id"]),
                now=now,
                clases=target_classes["cancelled"],
            )

        _ensure_reserva_confirmada(
            reserva_id=int(case["target_reserva_id"]),
            clase_id=case["target_clase"].clase_id,
            socio_id=socio_id,
            confirmada_en=now,
        )

        _ensure_pago_aprobado(
            socio_id=socio_id,
            reserva_id=int(case["target_reserva_id"]),
            monto=Decimal("1000.00"),
        )

    db.session.commit()

    print("✅ [SEED] Escenarios de reintegro listos:")
    print("   Password para todos: 123456.")
    for case in cases:
        print(
            f"   - {case['scenario']}: user={case['email']} / reserva_id={case['target_reserva_id']}"
        )


def _get_or_create_role(role_name: str) -> Rol:
    normalized = (role_name or "").strip().lower()
    role = Rol.query.filter(db.func.lower(Rol.nombre) == normalized).first()
    if role is not None:
        return role

    role = Rol(nombre=normalized, descripcion=f"Rol seed {normalized}.")
    db.session.add(role)
    db.session.flush()
    return role


def _ensure_socio_user(*, email: str, dni: str, nombre: str, apellido: str, rol: Rol) -> int:
    normalized_email = (email or "").strip().lower()
    normalized_dni = (dni or "").strip()

    persona = Persona.query.filter_by(email=normalized_email).first()
    if persona is None:
        persona = Persona.query.filter_by(dni=normalized_dni).first()

    password_hash = bcrypt.generate_password_hash(DEFAULT_PASSWORD).decode("utf-8")

    if persona is None:
        persona = Persona(
            dni=normalized_dni,
            email=normalized_email,
            password_hash=password_hash,
            nombre=nombre,
            apellido=apellido,
            telefono="2215003990",
            calle="Seed",
            numero_puerta="1",
            codigo_postal="1900",
            estado="activo",
            intereses="",
        )
        db.session.add(persona)
        db.session.flush()
    else:
        persona.dni = normalized_dni
        persona.email = normalized_email
        persona.nombre = nombre
        persona.apellido = apellido
        persona.estado = "activo"
        persona.password_hash = password_hash
        db.session.flush()

    socio = Socio.query.get(persona.persona_id)
    if socio is None:
        db.session.add(Socio(persona_id=persona.persona_id))
        db.session.flush()

    existing_roles = {assignment.rol_id for assignment in persona.persona_roles}
    if rol.rol_id not in existing_roles:
        db.session.add(PersonaRolPuente(persona_id=persona.persona_id, rol_id=rol.rol_id))
        db.session.flush()

    return persona.persona_id


def _resolve_target_classes(now: datetime):
    all_classes = Clase.query.order_by(Clase.fecha.asc(), Clase.horario_inicio.asc()).all()
    future_classes = [
        clase
        for clase in all_classes
        if _clase_inicio(clase) > now
    ]

    refund_class = next(
        (
            clase
            for clase in future_classes
            if _clase_inicio(clase) - now > timedelta(hours=48)
        ),
        None,
    )
    no_refund_class = next(
        (
            clase
            for clase in future_classes
            if timedelta(0) < _clase_inicio(clase) - now <= timedelta(hours=48)
        ),
        None,
    )

    if refund_class is None or no_refund_class is None:
        return None

    excluded_ids = {refund_class.clase_id, no_refund_class.clase_id}
    cancelled_classes = [
        clase for clase in all_classes if clase.clase_id not in excluded_ids
    ][:3]

    if len(cancelled_classes) < 3:
        return None

    return {
        "refund": refund_class,
        "no_refund": no_refund_class,
        "cancelled": cancelled_classes,
    }


def _clase_inicio(clase: Clase) -> datetime:
    return datetime.combine(clase.fecha, clase.horario_inicio).replace(tzinfo=timezone.utc)


def _ensure_reserva_confirmada(*, reserva_id: int, clase_id: int, socio_id: int, confirmada_en: datetime):
    reserva = Reserva.query.get(reserva_id)
    if reserva is None:
        reserva = Reserva(
            reserva_id=reserva_id,
            clase_id=clase_id,
            socio_id=socio_id,
            tipo_reserva="espontanea",
            estado="confirmada",
            confirmada_en=confirmada_en,
        )
        db.session.add(reserva)
        db.session.flush()
        return

    reserva.clase_id = clase_id
    reserva.socio_id = socio_id
    reserva.tipo_reserva = "espontanea"
    reserva.estado = "confirmada"
    reserva.confirmada_en = confirmada_en
    reserva.cancelada_en = None
    db.session.flush()


def _ensure_pago_aprobado(*, socio_id: int, reserva_id: int, monto: Decimal):
    pago = (
        Pago.query.filter_by(reserva_id=reserva_id)
        .order_by(Pago.pago_id.desc())
        .first()
    )

    external_ref = f"seed-ref-{reserva_id}-{uuid.uuid4()}"

    if pago is None:
        pago = Pago(
            socio_id=socio_id,
            reserva_id=reserva_id,
            proveedor="mercadopago",
            external_ref=external_ref,
            monto_bruto=monto,
            descuento_pct=Decimal("0"),
            monto_pagado=monto,
            estado="aprobado",
            fecha_pago=datetime.now(timezone.utc),
        )
        db.session.add(pago)
        db.session.flush()
        return

    pago.socio_id = socio_id
    pago.reserva_id = reserva_id
    pago.proveedor = "mercadopago"
    pago.external_ref = pago.external_ref or external_ref
    pago.monto_bruto = monto
    pago.descuento_pct = Decimal("0")
    pago.monto_pagado = monto
    pago.estado = "aprobado"
    pago.fecha_pago = pago.fecha_pago or datetime.now(timezone.utc)
    db.session.flush()


def _ensure_cancelled_reservas_in_month(*, socio_id: int, base_reserva_id: int, now: datetime, clases: list[Clase]):
    inicio_mes = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    for offset, clase in enumerate(clases, start=1):
        reserva_id = base_reserva_id + offset

        reserva = Reserva.query.get(reserva_id)
        if reserva is None:
            reserva = Reserva(
                reserva_id=reserva_id,
                clase_id=clase.clase_id,
                socio_id=socio_id,
                tipo_reserva="espontanea",
                estado="cancelada",
                confirmada_en=inicio_mes + timedelta(hours=offset),
                cancelada_en=inicio_mes + timedelta(hours=offset + 1),
            )
            db.session.add(reserva)
        else:
            reserva.clase_id = clase.clase_id
            reserva.socio_id = socio_id
            reserva.tipo_reserva = "espontanea"
            reserva.estado = "cancelada"
            reserva.confirmada_en = reserva.confirmada_en or (inicio_mes + timedelta(hours=offset))
            reserva.cancelada_en = inicio_mes + timedelta(hours=offset + 1)

        db.session.flush()
