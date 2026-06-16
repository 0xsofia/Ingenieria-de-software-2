from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import uuid

from src.core.bcrypt_and_session import bcrypt
from src.core.database import db
from src.core.models.clase import Clase
from src.core.models.pago import Pago
from src.core.models.persona import Persona, PersonaRolPuente, Rol, Socio
from src.core.models.reserva import Reserva
from src.core.models.lista_espera import ListaEspera

DEFAULT_PASSWORD = "123456."


def seed_bloqueos_escenarios(seed_datetime=None):
    if seed_datetime is None:
        now = datetime.now(timezone.utc)
    elif seed_datetime.tzinfo is None:
        now = seed_datetime.replace(tzinfo=timezone.utc)
    else:
        now = seed_datetime.astimezone(timezone.utc)

    target_classes = _resolve_target_classes(now)
    if not target_classes:
        print("⚠️  [SEED] No hay clases base suficientes; se omiten seeds de bloqueos.")
        return

    clase1 = target_classes[0]
    clase2 = target_classes[1] if len(target_classes) > 1 else target_classes[0]
    clase3 = target_classes[2] if len(target_classes) > 2 else target_classes[0]

    rol_socio = _get_or_create_role("socio")

    # Escenario 1: Bloqueo sin reservas activas
    _ensure_socio_user(
        email="bloqueo1@centro.test",
        dni="40000001",
        nombre="Bloqueo1",
        apellido="SinReservas",
        rol=rol_socio,
    )

    # Escenario 2: Bloqueo con devolución (reserva activa + pago)
    socio2_id = _ensure_socio_user(
        email="bloqueo2@centro.test",
        dni="40000002",
        nombre="Bloqueo2",
        apellido="ConDevolucion",
        rol=rol_socio,
    )
    _ensure_reserva_confirmada(
        reserva_id=8102,
        clase_id=clase1.clase_id,
        socio_id=socio2_id,
        confirmada_en=now,
    )
    _ensure_pago_aprobado(
        socio_id=socio2_id,
        reserva_id=8102,
        monto=Decimal("1500.00"),
    )

    # Escenario 3/4: Bloqueo sin devolución / sin lista de espera (reserva activa sin pago, o con pago q no importa)
    socio3_id = _ensure_socio_user(
        email="bloqueo3@centro.test",
        dni="40000003",
        nombre="Bloqueo3",
        apellido="SinDevolucion",
        rol=rol_socio,
    )
    _ensure_reserva_confirmada(
        reserva_id=8103,
        clase_id=clase2.clase_id,
        socio_id=socio3_id,
        confirmada_en=now,
    )
    _ensure_pago_aprobado(
        socio_id=socio3_id,
        reserva_id=8103,
        monto=Decimal("1500.00"),
    )

    # Escenario 5: Bloqueo con reserva activa y con usuario en lista de espera
    socio5_id = _ensure_socio_user(
        email="bloqueo5@centro.test",
        dni="40000005",
        nombre="Bloqueo5",
        apellido="ConListaEspera",
        rol=rol_socio,
    )
    _ensure_reserva_confirmada(
        reserva_id=8105,
        clase_id=clase3.clase_id,
        socio_id=socio5_id,
        confirmada_en=now,
    )
    socio_espera_id = _ensure_socio_user(
        email="espera_bloqueo@centro.test",
        dni="40000006",
        nombre="Espera",
        apellido="ParaBloqueo",
        rol=rol_socio,
    )
    _ensure_lista_espera(
        clase_id=clase3.clase_id,
        socio_id=socio_espera_id,
        posicion=1,
    )

    # HU-51: Usuario ya bloqueado para probar desbloqueo
    socio_bloqueado_id = _ensure_socio_user(
        email="bloqueado@centro.test",
        dni="40000007",
        nombre="Usuario",
        apellido="YaBloqueado",
        rol=rol_socio,
    )
    _bloquear_usuario(socio_bloqueado_id, "Socio problemático")

    db.session.commit()

    print("✅ [SEED] Escenarios de bloqueo/desbloqueo listos:")
    print("   Password para todos: 123456.")
    print("   - bloqueo1@centro.test (Escenario 1)")
    print("   - bloqueo2@centro.test (Escenario 2 - Con reserva y pago)")
    print("   - bloqueo3@centro.test (Escenario 3/4 - Sin devolución)")
    print("   - bloqueo5@centro.test (Escenario 5 - Con lista de espera)")
    print("   - bloqueado@centro.test (HU-51 - Para desbloquear)")


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
            telefono="2215004000",
            calle="Seed Bloqueo",
            numero_puerta="2",
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
        # We don't touch estado here because _bloquear_usuario handles it for blocked user
        if persona.estado != "bloqueado":
            persona.estado = "activo"
            persona.motivo_bloqueo = None
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


def _bloquear_usuario(persona_id: int, motivo: str):
    persona = Persona.query.get(persona_id)
    if persona:
        persona.estado = "bloqueado"
        persona.motivo_bloqueo = motivo
        db.session.flush()


def _resolve_target_classes(now: datetime):
    all_classes = Clase.query.order_by(Clase.fecha.asc(), Clase.horario_inicio.asc()).all()
    future_classes = [
        clase
        for clase in all_classes
        if _clase_inicio(clase) > now
    ]

    return future_classes


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

    external_ref = f"seed-block-{reserva_id}-{uuid.uuid4()}"

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


def _ensure_lista_espera(*, clase_id: int, socio_id: int, posicion: int):
    entry = ListaEspera.query.filter_by(clase_id=clase_id, socio_id=socio_id).first()
    if entry is None:
        entry = ListaEspera(
            clase_id=clase_id,
            socio_id=socio_id,
            posicion=posicion,
            estado="pendiente",
        )
        db.session.add(entry)
    else:
        entry.posicion = posicion
        entry.estado = "pendiente"
    db.session.flush()
