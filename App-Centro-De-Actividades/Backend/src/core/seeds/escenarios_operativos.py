from __future__ import annotations

import calendar
from datetime import datetime, time, timedelta
from decimal import Decimal

from src.core.bcrypt_and_session import bcrypt
from src.core.database import db
from src.core.enums.clase_enum import ActividadEnum, NivelEnum, TipoClaseEnum
from src.core.models.abono_mensual import AbonoMensual
from src.core.models.actividad import Actividad
from src.core.models.clase import Clase
from src.core.models.persona import Persona, PersonaRolPuente, Rol, Socio
from src.core.models.profesor import Profesor
from src.core.models.reserva import Reserva
from src.core.seeds.clases import get_seed_reference_datetime

DEFAULT_PASSWORD = "123456."


def seed_escenarios_operativos(seed_datetime=None):
    reference = get_seed_reference_datetime(seed_datetime)
    rol_socio = _get_or_create_role("socio")

    mate_id = _ensure_socio_user(
        email="mate@centro.test",
        dni="40000004",
        nombre="Mateo",
        apellido="Centro",
        rol=rol_socio,
    )

    _ensure_reserva_abonada_mes_actual(reference, mate_id)
    _ensure_reserva_abonada_menos_24_horas(reference, mate_id)
    _ensure_clase_extender_con_profesor_ocupado(reference)
    _ensure_clase_sin_reservas(reference)

    db.session.commit()
    print("[SEED] Escenarios operativos listos:")
    print("   - mate@centro.test con reserva abonada del mes actual")
    print("   - mate@centro.test con reserva abonada a menos de 24 horas")
    print("   - clase para extender con profesor ocupado el mes siguiente")
    print("   - clase en cancha 'cancha sin reservas' sin reservas asociadas")


def _ensure_reserva_abonada_mes_actual(reference, socio_id):
    clase_datetime = _future_datetime_in_current_month(reference, days_ahead=7, hour=18)
    clase = _get_or_create_clase(
        actividad="Futbol",
        cancha="Cancha Abonada Mes Actual",
        nivel="Intermedio",
        cupos=8,
        profesor_dni="87654321",
        precio=Decimal("1000.00"),
        fecha=clase_datetime.date(),
        horario_inicio=clase_datetime.time(),
    )
    abono = _get_or_create_abono(
        socio_id=socio_id,
        actividad_nombre="Futbol",
        periodo_inicio=reference.date().replace(day=1),
        periodo_fin=_last_day_of_month(reference.date()),
        hora_inicio=clase.horario_inicio,
        dia_semana=_dia_semana_label(clase.fecha),
        descuento_aplicado_pct=20,
    )
    _ensure_reserva_abonada(
        reserva_id=9401,
        clase_id=clase.clase_id,
        socio_id=socio_id,
        abono_mensual_id=abono.abono_mensual_id,
        timestamp=reference,
    )


def _ensure_reserva_abonada_menos_24_horas(reference, socio_id):
    clase_datetime = (reference + timedelta(hours=12)).replace(
        minute=0, second=0, microsecond=0
    )
    if clase_datetime <= reference:
        clase_datetime += timedelta(hours=1)

    clase = _get_or_create_clase(
        actividad="Voley",
        cancha="Cancha Abonada Cancelar 24h",
        nivel="Principiante",
        cupos=8,
        profesor_dni="12345678",
        precio=Decimal("1000.00"),
        fecha=clase_datetime.date(),
        horario_inicio=clase_datetime.time(),
    )
    abono = _get_or_create_abono(
        socio_id=socio_id,
        actividad_nombre="Voley",
        periodo_inicio=reference.date().replace(day=1),
        periodo_fin=_last_day_of_month(reference.date()),
        hora_inicio=clase.horario_inicio,
        dia_semana=_dia_semana_label(clase.fecha),
        descuento_aplicado_pct=20,
    )
    _ensure_reserva_abonada(
        reserva_id=9402,
        clase_id=clase.clase_id,
        socio_id=socio_id,
        abono_mensual_id=abono.abono_mensual_id,
        timestamp=reference,
    )


def _ensure_clase_extender_con_profesor_ocupado(reference):
    base_datetime = _next_weekday_datetime(reference, weekday=1, hour=16)
    conflict_date = _first_weekday_of_next_month(reference.date(), base_datetime.weekday())
    conflict_datetime = datetime.combine(conflict_date, base_datetime.time()).replace(
        tzinfo=reference.tzinfo
    )

    _get_or_create_clase(
        actividad="Basquet",
        cancha="Cancha Extender Base",
        nivel="Intermedio",
        cupos=10,
        profesor_dni="11223344",
        precio=Decimal("1200.00"),
        fecha=base_datetime.date(),
        horario_inicio=base_datetime.time(),
    )
    _get_or_create_clase(
        actividad="Basquet",
        cancha="Cancha Profesor Ocupado Mes Siguiente",
        nivel="Intermedio",
        cupos=10,
        profesor_dni="11223344",
        precio=Decimal("1200.00"),
        fecha=conflict_datetime.date(),
        horario_inicio=conflict_datetime.time(),
    )


def _ensure_clase_sin_reservas(reference):
    clase_datetime = _next_weekday_datetime(reference, weekday=3, hour=17)
    clase = _get_or_create_clase_por_cancha(
        actividad="Futbol",
        cancha="cancha sin reservas",
        nivel="Principiante",
        cupos=10,
        profesor_dni="44332211",
        precio=Decimal("900.00"),
        fecha=clase_datetime.date(),
        horario_inicio=clase_datetime.time(),
    )

    Reserva.query.filter_by(clase_id=clase.clase_id).delete(synchronize_session=False)


def _get_or_create_clase_por_cancha(
    *,
    actividad,
    cancha,
    nivel,
    cupos,
    profesor_dni,
    precio,
    fecha,
    horario_inicio,
):
    clase = Clase.query.filter_by(cancha=cancha).first()
    if clase is None:
        return _get_or_create_clase(
            actividad=actividad,
            cancha=cancha,
            nivel=nivel,
            cupos=cupos,
            profesor_dni=profesor_dni,
            precio=precio,
            fecha=fecha,
            horario_inicio=horario_inicio,
        )

    profesor = Profesor.query.filter_by(dni=profesor_dni).first()
    if profesor is None:
        raise RuntimeError(f"No existe el profesor con DNI {profesor_dni}.")

    clase.actividad = ActividadEnum(actividad)
    clase.fecha = fecha
    clase.horario_inicio = horario_inicio
    clase.horario_fin = (datetime.combine(fecha, horario_inicio) + timedelta(hours=1)).time()
    clase.nivel = NivelEnum(nivel)
    clase.cupos = cupos
    clase.precio = precio
    clase.tipo_clase = TipoClaseEnum.PARTICULAR if int(cupos) == 1 else TipoClaseEnum.GRUPAL
    clase.profesor_id = profesor.profesor_id
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
            telefono="2215003991",
            calle="Seed",
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
        persona.estado = "activo"
        persona.password_hash = password_hash
        db.session.flush()

    if persona.socio is None:
        db.session.add(Socio(persona_id=persona.persona_id))
        db.session.flush()

    existing_roles = {assignment.rol_id for assignment in persona.persona_roles}
    if rol.rol_id not in existing_roles:
        db.session.add(PersonaRolPuente(persona_id=persona.persona_id, rol_id=rol.rol_id))
        db.session.flush()

    return persona.persona_id


def _get_or_create_clase(
    *,
    actividad,
    cancha,
    nivel,
    cupos,
    profesor_dni,
    precio,
    fecha,
    horario_inicio,
):
    profesor = Profesor.query.filter_by(dni=profesor_dni).first()
    if profesor is None:
        raise RuntimeError(f"No existe el profesor con DNI {profesor_dni}.")

    horario_fin = (datetime.combine(fecha, horario_inicio) + timedelta(hours=1)).time()
    actividad_enum = ActividadEnum(actividad)

    clase = Clase.query.filter_by(
        profesor_id=profesor.profesor_id,
        fecha=fecha,
        horario_inicio=horario_inicio,
        actividad=actividad_enum,
    ).first()

    tipo_clase = TipoClaseEnum.PARTICULAR if int(cupos) == 1 else TipoClaseEnum.GRUPAL

    if clase is None:
        clase = Clase(
            actividad=actividad_enum,
            fecha=fecha,
            horario_inicio=horario_inicio,
            horario_fin=horario_fin,
            cancha=cancha,
            nivel=NivelEnum(nivel),
            cupos=cupos,
            precio=precio,
            tipo_clase=tipo_clase,
            profesor_id=profesor.profesor_id,
        )
        db.session.add(clase)
    else:
        clase.cancha = cancha
        clase.nivel = NivelEnum(nivel)
        clase.cupos = cupos
        clase.precio = precio
        clase.tipo_clase = tipo_clase
        clase.horario_fin = horario_fin
        clase.is_eliminated = False

    db.session.flush()
    return clase


def _get_or_create_abono(
    *,
    socio_id,
    actividad_nombre,
    periodo_inicio,
    periodo_fin,
    hora_inicio,
    dia_semana,
    descuento_aplicado_pct,
):
    actividad = Actividad.query.filter_by(nombre=actividad_nombre).first()
    if actividad is None:
        raise RuntimeError(f"No existe la actividad {actividad_nombre}.")

    abono = (
        AbonoMensual.query.filter_by(
            socio_id=socio_id,
            actividad_id=actividad.actividad_id,
            periodo_inicio=periodo_inicio,
            hora_inicio=hora_inicio,
        )
        .first()
    )

    if abono is None:
        abono = AbonoMensual(
            socio_id=socio_id,
            actividad_id=actividad.actividad_id,
            periodo_inicio=periodo_inicio,
            periodo_fin=periodo_fin,
            hora_inicio=hora_inicio,
            dia_semana=dia_semana,
            descuento_aplicado_pct=descuento_aplicado_pct,
            prioridad_renovacion=False,
            fecha_limite_renovacion=None,
            estado="activo",
        )
        db.session.add(abono)
    else:
        abono.periodo_fin = periodo_fin
        abono.dia_semana = dia_semana
        abono.descuento_aplicado_pct = descuento_aplicado_pct
        abono.estado = "activo"

    db.session.flush()
    return abono


def _ensure_reserva_abonada(
    *, reserva_id, clase_id, socio_id, abono_mensual_id, timestamp
):
    reserva = Reserva.query.get(reserva_id)
    if reserva is None:
        reserva = Reserva(
            reserva_id=reserva_id,
            clase_id=clase_id,
            socio_id=socio_id,
            abono_mensual_id=abono_mensual_id,
            tipo_reserva="abonada",
            estado="confirmada",
            creada_en=timestamp,
            confirmada_en=timestamp,
        )
        db.session.add(reserva)
    else:
        reserva.clase_id = clase_id
        reserva.socio_id = socio_id
        reserva.abono_mensual_id = abono_mensual_id
        reserva.tipo_reserva = "abonada"
        reserva.estado = "confirmada"
        reserva.confirmada_en = reserva.confirmada_en or timestamp
        reserva.cancelada_en = None

    db.session.flush()


def _future_datetime_in_current_month(reference, *, days_ahead, hour):
    candidate = (reference + timedelta(days=days_ahead)).replace(
        hour=hour, minute=0, second=0, microsecond=0
    )
    last_day = _last_day_of_month(reference.date())
    if candidate.date() <= last_day:
        return candidate

    return datetime.combine(last_day, time(hour=hour)).replace(tzinfo=reference.tzinfo)


def _next_weekday_datetime(reference, *, weekday, hour):
    days_until = (weekday - reference.weekday()) % 7
    candidate = (reference + timedelta(days=days_until)).replace(
        hour=hour, minute=0, second=0, microsecond=0
    )
    if candidate <= reference:
        candidate += timedelta(days=7)
    return candidate


def _first_weekday_of_next_month(reference_date, weekday):
    year = reference_date.year + (1 if reference_date.month == 12 else 0)
    month = 1 if reference_date.month == 12 else reference_date.month + 1
    first_day = reference_date.replace(year=year, month=month, day=1)
    days_until_weekday = (weekday - first_day.weekday()) % 7
    return first_day + timedelta(days=days_until_weekday)


def _last_day_of_month(reference_date):
    last_day = calendar.monthrange(reference_date.year, reference_date.month)[1]
    return reference_date.replace(day=last_day)


def _dia_semana_label(fecha):
    dias = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
    return dias[fecha.weekday()]
