from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid

from src.core.bcrypt_and_session import bcrypt
from src.core.database import db
from src.core.enums.clase_enum import ActividadEnum, NivelEnum, TipoClaseEnum
from src.core.models.clase import Clase
from src.core.models.pago import Pago
from src.core.models.persona import Persona, PersonaRolPuente, Rol, Socio
from src.core.models.profesor import Profesor
from src.core.models.reserva import Reserva

DEFAULT_PASSWORD = "123456."


def seed_reintegros_escenarios():
    """Crea datos semilla para probar los 4 escenarios de reintegro.

    Escenarios (ver src.core.services.reservas.cancelar_reserva_espontanea):
      - escenario_1: reintegro_aplica=True,  sancion_aplicada=False
      - escenario_2: reintegro_aplica=False, sancion_aplicada=False
      - escenario_3: reintegro_aplica=True,  sancion_aplicada=True
      - escenario_4: reintegro_aplica=False, sancion_aplicada=True

    Nota: Para escenario_3/4 se precargan 3 cancelaciones en el mes.
    """

    now = datetime.now(timezone.utc)

    profesor = Profesor.query.order_by(Profesor.profesor_id.asc()).first()
    if profesor is None:
        print("⚠️  [SEED] No hay profesores; se omiten seeds de reintegros.")
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
            "start_delta": timedelta(days=7),
            "needs_sancion": False,
        },
        {
            "scenario": "escenario_2",
            "email": "reintegro2@centro.test",
            "dni": "39900002",
            "nombre": "Reintegro",
            "apellido": "Escenario2",
            "target_reserva_id": 9102,
            "start_delta": timedelta(hours=6),
            "needs_sancion": False,
        },
        {
            "scenario": "escenario_3",
            "email": "reintegro3@centro.test",
            "dni": "39900003",
            "nombre": "Reintegro",
            "apellido": "Escenario3",
            "target_reserva_id": 9103,
            "start_delta": timedelta(days=7),
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
            "start_delta": timedelta(hours=6),
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
                profesor_id=profesor.profesor_id,
                base_reserva_id=int(case["cancelled_base_id"]),
                now=now,
            )

        start_dt = now + case["start_delta"]
        clase = _ensure_clase(
            profesor_id=profesor.profesor_id,
            start_dt=start_dt,
            cancha=f"Seed {case['scenario']}",
            precio=Decimal("1000.00"),
        )

        _ensure_reserva_confirmada(
            reserva_id=int(case["target_reserva_id"]),
            clase_id=clase.clase_id,
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


def _ensure_clase(*, profesor_id: int, start_dt: datetime, cancha: str, precio: Decimal) -> Clase:
    start_dt = start_dt.astimezone(timezone.utc)

    fecha = start_dt.date()
    horario_inicio = start_dt.time().replace(second=0, microsecond=0)
    horario_fin = (start_dt + timedelta(hours=1)).time().replace(second=0, microsecond=0)

    clase = (
        Clase.query.filter_by(
            actividad=ActividadEnum.FUTBOL,
            fecha=fecha,
            horario_inicio=horario_inicio,
            cancha=cancha,
        )
        .order_by(Clase.clase_id.asc())
        .first()
    )

    if clase is None:
        clase = Clase(
            actividad=ActividadEnum.FUTBOL,
            fecha=fecha,
            horario_inicio=horario_inicio,
            horario_fin=horario_fin,
            cancha=cancha,
            nivel=NivelEnum.PRINCIPIANTE,
            cupos=10,
            precio=precio,
            tipo_clase=TipoClaseEnum.GRUPAL,
            profesor_id=profesor_id,
        )
        db.session.add(clase)
        db.session.flush()
        return clase

    clase.horario_fin = horario_fin
    clase.nivel = NivelEnum.PRINCIPIANTE
    clase.cupos = 10
    clase.precio = precio
    clase.tipo_clase = TipoClaseEnum.GRUPAL
    clase.profesor_id = profesor_id
    db.session.flush()

    return clase


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


def _ensure_cancelled_reservas_in_month(*, socio_id: int, profesor_id: int, base_reserva_id: int, now: datetime):
    inicio_mes = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    for offset in range(1, 4):
        reserva_id = base_reserva_id + offset
        start_dt = now + timedelta(days=10 + offset)
        clase = _ensure_clase(
            profesor_id=profesor_id,
            start_dt=start_dt,
            cancha=f"Seed sancion {base_reserva_id}-{offset}",
            precio=Decimal("500.00"),
        )

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
