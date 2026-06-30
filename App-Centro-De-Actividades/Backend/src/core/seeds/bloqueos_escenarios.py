from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
import uuid

from src.core.bcrypt_and_session import bcrypt
from src.core.database import db
from src.core.enums.clase_enum import ActividadEnum, NivelEnum, TipoClaseEnum
from src.core.models.abono_mensual import AbonoMensual
from src.core.models.actividad import Actividad
from src.core.models.clase import Clase
from src.core.models.lista_espera import ListaEspera
from src.core.models.pago import Pago
from src.core.models.persona import Persona, PersonaRolPuente, Rol, Socio
from src.core.models.profesor import Profesor
from src.core.models.reserva import Reserva
from src.core.seeds.clases import get_seed_reference_datetime

DEFAULT_PASSWORD = "123456."

BLOQUEO_CLASS_TEMPLATES = {
    "sin_lista_espera": {
        "actividad": "Futbol",
        "cancha": "Cancha Bloqueo 1",
        "nivel": "Intermedio",
        "cupos": 1,
        "profesor_dni": "87654321",
        "precio": Decimal("5000.00"),
        "dias_despues": 4,
        "hora": 18,
        "minuto": 0,
    },
    "con_lista_espera": {
        "actividad": "Voley",
        "cancha": "Cancha Bloqueo 2",
        "nivel": "Principiante",
        "cupos": 1,
        "profesor_dni": "12345678",
        "precio": Decimal("5000.00"),
        "dias_despues": 4,
        "hora": 18,
        "minuto": 0,
    },
    "conflicto_lista_espera": {
        "actividad": "Futbol",
        "cancha": "Cancha Bloqueo 4",
        "nivel": "Principiante",
        "cupos": 1,
        "profesor_dni": "12345678",
        "precio": Decimal("5000.00"),
        "dias_despues": 4,
        "hora": 18,
        "minuto": 0,
    },
    "abandonar_espera": {
        "actividad": "Basquet",
        "cancha": "Cancha Bloqueo 3",
        "nivel": "Principiante",
        "cupos": 1,
        "profesor_dni": "12345678",
        "precio": Decimal("5000.00"),
        "dias_despues": 5,
        "hora": 19,
        "minuto": 0,
    },
}

RENOVACION_ACTIVIDAD = "Futbol"
RENOVACION_HORA = time(19, 0)
RENOVACION_CLASES_JUNIO_2026 = (
    date(2026, 6, 1),
    date(2026, 6, 8),
    date(2026, 6, 15),
    date(2026, 6, 22),
)


def seed_bloqueos_escenarios(seed_datetime=None):
    now = _as_utc(seed_datetime)
    rol_socio = _get_or_create_role("socio")
    clases = _ensure_bloqueo_classes(seed_datetime)

    # bloqueo1: escenario 1 de bloqueo y escenario 2 de desbloqueo.
    bloqueo1_id = _ensure_socio_user(
        email="bloqueo1@centro.test",
        dni="40000001",
        nombre="Juan",
        apellido="Perez",
        rol=rol_socio,
    )
    _set_sancion(bloqueo1_id, None)

    # bloqueo2: escenarios 2 y 4, con reserva paga y sin lista de espera.
    bloqueo2_id = _ensure_socio_user(
        email="bloqueo2@centro.test",
        dni="40000002",
        nombre="Juan",
        apellido="Perez",
        rol=rol_socio,
    )
    _set_sancion(bloqueo2_id, now.date() + timedelta(days=30))
    _ensure_reserva_confirmada(
        reserva_id=8102,
        clase_id=clases["sin_lista_espera"].clase_id,
        socio_id=bloqueo2_id,
        confirmada_en=now,
    )
    _ensure_pago_aprobado(
        socio_id=bloqueo2_id,
        reserva_id=8102,
        monto=Decimal("5000.00"),
    )

    # bloqueo3: escenarios 3 y 5, con reserva paga y socio siguiente en espera.
    bloqueo3_id = _ensure_socio_user(
        email="bloqueo3@centro.test",
        dni="40000003",
        nombre="Juan",
        apellido="Perez",
        rol=rol_socio,
    )
    _set_sancion(bloqueo3_id, None)
    _ensure_reserva_confirmada(
        reserva_id=8103,
        clase_id=clases["con_lista_espera"].clase_id,
        socio_id=bloqueo3_id,
        confirmada_en=now,
    )
    _ensure_pago_aprobado(
        socio_id=bloqueo3_id,
        reserva_id=8103,
        monto=Decimal("5000.00"),
    )

    # bloqueo4: escenario para probar superposición de horarios al confirmar un turno.
    bloqueo4_id = _ensure_socio_user(
        email="bloqueo4@centro.test",
        dni="40000008",
        nombre="Juan",
        apellido="Cuatro",
        rol=rol_socio,
    )
    _set_sancion(bloqueo4_id, None)
    _ensure_reserva_confirmada(
        reserva_id=8105,
        clase_id=clases["conflicto_lista_espera"].clase_id,
        socio_id=bloqueo4_id,
        confirmada_en=now,
    )
    _ensure_pago_aprobado(
        socio_id=bloqueo4_id,
        reserva_id=8105,
        monto=Decimal("5000.00"),
    )

    mate_id = _ensure_socio_user(
        email="mate@centro.test",
        dni="40000004",
        nombre="Mateo",
        apellido="Centro",
        rol=rol_socio,
        password="123456.",
    )
    _set_sancion(mate_id, None)

    sancion_id = _ensure_socio_user(
        email="sancion@centro.test",
        dni="40000006",
        nombre="Sancion",
        apellido="Centro",
        rol=rol_socio,
        password="123456.",
    )
    _set_sancion(sancion_id, date(2026, 6, 30))

    renovacion_clases = _ensure_renovacion_classes()
    _ensure_abono_renovable(
        socio_id=mate_id,
        actividad_nombre=RENOVACION_ACTIVIDAD,
    )
    _ensure_abono_expirado_mate(mate_id)
    _ensure_abono_renovable(
        socio_id=sancion_id,
        actividad_nombre=RENOVACION_ACTIVIDAD,
    )

    # 1) Waitlist test "confirmar turno" (Waitlist 2)
    _ensure_lista_espera(
        clase_id=clases["con_lista_espera"].clase_id,
        socio_id=mate_id,
        posicion=1,
    )
    
    # 1.5) Waitlist para test de conflicto horario (Waitlist)
    _ensure_lista_espera(
        clase_id=clases["conflicto_lista_espera"].clase_id,
        socio_id=mate_id,
        posicion=1,
    )

    # 2) Waitlist test "abandonar lista de espera" (Waitlist 1)
    dummy_id = _ensure_socio_user(
        email="dummy_abandonar@centro.test",
        dni="40000005",
        nombre="Dummy",
        apellido="Ocupa",
        rol=rol_socio,
    )
    _set_sancion(dummy_id, None)
    _ensure_reserva_confirmada(
        reserva_id=8104,
        clase_id=clases["abandonar_espera"].clase_id,
        socio_id=dummy_id,
        confirmada_en=now,
    )
    _ensure_pago_aprobado(
        socio_id=dummy_id,
        reserva_id=8104,
        monto=Decimal("5000.00"),
    )

    _ensure_lista_espera(
        clase_id=clases["abandonar_espera"].clase_id,
        socio_id=mate_id,
        posicion=1,
    )

    db.session.commit()

    print("[SEED] Escenarios de bloqueo/desbloqueo listos:")
    print("   Password general: 123456.")
    print("   - bloqueo1@centro.test (sin reservas, sin sanciones)")
    print("   - bloqueo2@centro.test (reserva paga, sin lista de espera, con sanciones)")
    print("   - bloqueo3@centro.test (reserva paga, con lista de espera)")
    print("   - bloqueo4@centro.test (reserva paga, para superposición de horarios)")
    print("   - mate@centro.test (siguiente en 3 listas de espera)")
    print(
        "   - mate@centro.test y sancion@centro.test "
        f"(abonos renovables hacia clase {renovacion_clases[0].fecha:%d/%m/%Y})"
    )


def _as_utc(seed_datetime=None):
    if seed_datetime is None:
        return datetime.now(timezone.utc)

    if seed_datetime.tzinfo is None:
        return seed_datetime.replace(tzinfo=timezone.utc)

    return seed_datetime.astimezone(timezone.utc)


def _ensure_bloqueo_classes(seed_datetime=None):
    reference = get_seed_reference_datetime(seed_datetime)
    classes = {}

    for key, template in BLOQUEO_CLASS_TEMPLATES.items():
        class_datetime = reference.replace(
            hour=template["hora"],
            minute=template["minuto"],
            second=0,
            microsecond=0,
        ) + timedelta(days=template["dias_despues"])
        classes[key] = _get_or_create_clase(
            {
                **template,
                "fecha": class_datetime.date(),
                "horario_inicio": class_datetime.time(),
            }
        )

    return classes


def _get_or_create_clase(clase_data):
    profesor = Profesor.query.filter_by(dni=clase_data["profesor_dni"]).first()
    if profesor is None:
        raise RuntimeError(
            f"No existe el profesor con DNI {clase_data['profesor_dni']} para el seed de bloqueos."
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


def _get_or_create_role(role_name: str) -> Rol:
    normalized = (role_name or "").strip().lower()
    role = Rol.query.filter(db.func.lower(Rol.nombre) == normalized).first()
    if role is not None:
        return role

    role = Rol(nombre=normalized, descripcion=f"Rol seed {normalized}.")
    db.session.add(role)
    db.session.flush()
    return role


def _ensure_socio_user(
    *,
    email: str,
    dni: str,
    nombre: str,
    apellido: str,
    rol: Rol,
    password: str = DEFAULT_PASSWORD,
) -> int:
    normalized_email = (email or "").strip().lower()
    normalized_dni = (dni or "").strip()

    persona = Persona.query.filter_by(email=normalized_email).first()
    if persona is None:
        persona = Persona.query.filter_by(dni=normalized_dni).first()

    password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

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
    else:
        persona.dni = normalized_dni
        persona.email = normalized_email
        persona.nombre = nombre
        persona.apellido = apellido
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
        db.session.add(
            PersonaRolPuente(persona_id=persona.persona_id, rol_id=rol.rol_id)
        )
        db.session.flush()

    return persona.persona_id


def _set_sancion(persona_id: int, blocked_until):
    socio = Socio.query.get(persona_id)
    if socio is not None:
        socio.descuento_bloqueado_hasta = blocked_until
        db.session.flush()


def _ensure_actividad(nombre: str) -> Actividad:
    actividad = Actividad.query.filter_by(nombre=nombre).first()
    if actividad is not None:
        return actividad

    actividad = Actividad(nombre=nombre)
    db.session.add(actividad)
    db.session.flush()
    return actividad


def _ensure_renovacion_classes():
    profesor = Profesor.query.filter_by(dni="87654321").first()
    if profesor is None:
        raise RuntimeError(
            "No existe el profesor con DNI 87654321 para el seed de renovación."
        )

    clases = []
    for fecha in RENOVACION_CLASES_JUNIO_2026:
        clase = _get_or_create_clase(
            {
                "actividad": RENOVACION_ACTIVIDAD,
                "cancha": "Cancha Renovacion",
                "nivel": "Intermedio",
                "cupos": 8,
                "profesor_dni": profesor.dni,
                "precio": Decimal("1000.00"),
                "fecha": fecha,
                "horario_inicio": RENOVACION_HORA,
            }
        )
        clases.append(clase)

    return clases


def _ensure_abono_renovable(*, socio_id: int, actividad_nombre: str):
    actividad = _ensure_actividad(actividad_nombre)

    abono = (
        AbonoMensual.query.filter_by(
            socio_id=socio_id,
            actividad_id=actividad.actividad_id,
            periodo_inicio=date(2026, 5, 4),
        )
        .first()
    )

    if abono is None:
        abono = AbonoMensual(
            socio_id=socio_id,
            actividad_id=actividad.actividad_id,
            periodo_inicio=date(2026, 5, 4),
            periodo_fin=date(2026, 5, 25),
            hora_inicio=RENOVACION_HORA,
            dia_semana="lunes",
            fecha_limite_renovacion=date(2026, 6, 10),
            estado="activo",
        )
        db.session.add(abono)
    else:
        abono.periodo_fin = date(2026, 5, 25)
        abono.hora_inicio = RENOVACION_HORA
        abono.dia_semana = "lunes"
        abono.fecha_limite_renovacion = date(2026, 6, 10)
        abono.estado = "activo"
        abono.prioridad_renovacion = False

    db.session.flush()
    return abono


def _ensure_abono_expirado_mate(socio_id: int):
    actividad = _ensure_actividad("Voley")

    abono = (
        AbonoMensual.query.filter_by(
            socio_id=socio_id,
            actividad_id=actividad.actividad_id,
            periodo_inicio=date(2026, 4, 6),
        )
        .first()
    )

    if abono is None:
        abono = AbonoMensual(
            socio_id=socio_id,
            actividad_id=actividad.actividad_id,
            periodo_inicio=date(2026, 4, 6),
            periodo_fin=date(2026, 4, 27),
            hora_inicio=time(18, 0),
            dia_semana="lunes",
            fecha_limite_renovacion=date(2026, 5, 10),
            estado="activo",
        )
        db.session.add(abono)
    else:
        abono.periodo_fin = date(2026, 4, 27)
        abono.hora_inicio = time(18, 0)
        abono.dia_semana = "lunes"
        abono.fecha_limite_renovacion = date(2026, 5, 10)
        abono.estado = "activo"
        abono.prioridad_renovacion = False

    db.session.flush()
    return abono


def _ensure_reserva_confirmada(
    *, reserva_id: int, clase_id: int, socio_id: int, confirmada_en: datetime
):
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
    else:
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
    else:
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
