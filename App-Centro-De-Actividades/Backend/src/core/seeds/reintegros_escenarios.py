from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid

from src.core.bcrypt_and_session import bcrypt
from src.core.database import db
from src.core.enums.clase_enum import ActividadEnum, NivelEnum, TipoClaseEnum
from src.core.models.clase import Clase
from src.core.models.lista_espera import ListaEspera
from src.core.models.pago import Pago
from src.core.models.persona import Persona, PersonaRolPuente, Rol, Socio
from src.core.models.profesor import Profesor
from src.core.models.reserva import Reserva
from src.core.seeds.clases import get_seed_reference_datetime

DEFAULT_PASSWORD = "123456."

REINTEGROS_CLASS_TEMPLATES = {
    "refund": {
        "actividad": "Basquet",
        "cancha": "Cancha Reintegro 1",
        "nivel": "Principiante",
        "cupos": 10,
        "profesor_dni": "12345678",
        "precio": Decimal("5000.00"),
        "dias_despues": 3,
        "hora": 10,
        "minuto": 0,
    },
    "no_refund": {
        "actividad": "Voley",
        "cancha": "Cancha Reintegro 2",
        "nivel": "Intermedio",
        "cupos": 10,
        "profesor_dni": "87654321",
        "precio": Decimal("5000.00"),
        "dias_despues": 1,
        "hora": 10,
        "minuto": 0,
    },
    "cancelled_1": {
        "actividad": "Futbol",
        "cancha": "Cancha Reintegro 3",
        "nivel": "Principiante",
        "cupos": 10,
        "profesor_dni": "12345678",
        "precio": Decimal("5000.00"),
        "dias_despues": 5,
        "hora": 10,
        "minuto": 0,
    },
    "cancelled_2": {
        "actividad": "Futbol",
        "cancha": "Cancha Reintegro 4",
        "nivel": "Intermedio",
        "cupos": 10,
        "profesor_dni": "87654321",
        "precio": Decimal("5000.00"),
        "dias_despues": 6,
        "hora": 10,
        "minuto": 0,
    },
    "cancelled_3": {
        "actividad": "Futbol",
        "cancha": "Cancha Reintegro 5",
        "nivel": "Avanzado",
        "cupos": 10,
        "profesor_dni": "12345678",
        "precio": Decimal("5000.00"),
        "dias_despues": 7,
        "hora": 10,
        "minuto": 0,
    },
}

def seed_reintegros_escenarios(seed_datetime=None):
    """Crea datos semilla para probar los 4 escenarios de reintegro.

    Escenarios (ver src.core.services.reservas.cancelar_reserva_espontanea):
      - escenario_1: reintegro_aplica=True,  sancion_aplicada=False
      - escenario_2: reintegro_aplica=False, sancion_aplicada=False
      - escenario_3: reintegro_aplica=True,  sancion_aplicada=True
      - escenario_4: reintegro_aplica=False, sancion_aplicada=True

    Nota: Para escenario_3/4 se precargan 3 cancelaciones en el mes.
    """

    if seed_datetime is None:
        now = datetime.now(timezone.utc)
    elif seed_datetime.tzinfo is None:
        now = seed_datetime.replace(tzinfo=timezone.utc)
    else:
        now = seed_datetime.astimezone(timezone.utc)

    target_classes = _ensure_reintegros_classes(seed_datetime)
    if target_classes is None:
        print("⚠️  [SEED] Error generando clases de reintegro.")
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
            _set_sancion_descuento(socio_id, now.date() + timedelta(days=30))
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

    mate_id = _ensure_socio_user(
        email="mate@centro.test",
        dni="40000004",
        nombre="Mateo",
        apellido="Centro",
        rol=rol_socio,
    )
    for case in cases:
        _ensure_lista_espera(
            clase_id=case["target_clase"].clase_id,
            socio_id=mate_id,
            posicion=1,
        )

    db.session.commit()

    print("✅ [SEED] Escenarios de reintegro listos:")
    print("   Password para todos: 123456.")
    for case in cases:
        print(
            f"   - {case['scenario']}: user={case['email']} / reserva_id={case['target_reserva_id']}"
        )
    print("   - mate@centro.test en lista de espera de todos los reintegros (1, 2, 3 y 4)")


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


def _ensure_reintegros_classes(seed_datetime=None):
    reference = get_seed_reference_datetime(seed_datetime)
    classes = {}

    for key, template in REINTEGROS_CLASS_TEMPLATES.items():
        class_datetime = (
            reference.replace(
                hour=template["hora"],
                minute=template["minuto"],
                second=0,
                microsecond=0,
            )
            + timedelta(days=template["dias_despues"])
        )
        classes[key] = _get_or_create_clase(
            {
                **template,
                "fecha": class_datetime.date(),
                "horario_inicio": class_datetime.time(),
            }
        )

    return {
        "refund": classes["refund"],
        "no_refund": classes["no_refund"],
        "cancelled": [classes["cancelled_1"], classes["cancelled_2"], classes["cancelled_3"]],
    }


def _get_or_create_clase(clase_data):
    profesor = Profesor.query.filter_by(dni=clase_data["profesor_dni"]).first()
    if profesor is None:
        raise RuntimeError(
            f"No existe el profesor con DNI {clase_data['profesor_dni']} para el seed de reintegros."
        )

    actividad = ActividadEnum(clase_data["actividad"])
    nivel = NivelEnum(clase_data["nivel"])
    fecha = clase_data["fecha"]
    horario_inicio = clase_data["horario_inicio"]
    horario_fin = (datetime.combine(fecha, horario_inicio) + timedelta(hours=1)).time()

    clase = Clase.query.filter_by(
        profesor_id=profesor.profesor_id,
        fecha=fecha,
        horario_inicio=horario_inicio,
        actividad=actividad,
    ).first()

    tipo_clase = (
        TipoClaseEnum.PARTICULAR
        if int(clase_data["cupos"]) == 1
        else TipoClaseEnum.GRUPAL
    )

    if clase is None:
        clase = Clase(
            actividad=actividad,
            fecha=fecha,
            horario_inicio=horario_inicio,
            horario_fin=horario_fin,
            cancha=clase_data["cancha"],
            nivel=nivel,
            cupos=clase_data["cupos"],
            precio=clase_data["precio"],
            tipo_clase=tipo_clase,
            profesor_id=profesor.profesor_id,
        )
        db.session.add(clase)
    else:
        clase.cancha = clase_data["cancha"]
        clase.nivel = nivel
        clase.cupos = clase_data["cupos"]
        clase.precio = clase_data["precio"]
        clase.tipo_clase = tipo_clase
        clase.horario_fin = horario_fin
        clase.is_eliminated = False

    db.session.flush()
    return clase


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

    entry.notificado_en = None
    entry.vence_confirmacion_en = None
    entry.confirmada_en = None
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


def _set_sancion_descuento(socio_id: int, blocked_until):
    socio = Socio.query.get(socio_id)
    if socio is None:
        return

    socio.descuento_bloqueado_hasta = blocked_until
    db.session.flush()
