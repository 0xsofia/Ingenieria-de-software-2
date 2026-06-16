from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from src.core.database import db
from src.core.models.persona import Persona, PersonaRolPuente
from src.core.services.registrarse import (
    normalizar_email,
    validar_payload_registro_empleado,
)

USER_UPDATED_MESSAGE = "El usuario ha sido actualizado con éxito."


def listar_usuarios(filters=None):
    normalized_filters = _normalizar_filtros_listado(filters)

    query = Persona.query.options(
        joinedload(Persona.empleado),
        joinedload(Persona.socio),
        joinedload(Persona.persona_roles).joinedload(PersonaRolPuente.rol),
    ).filter(db.or_(Persona.empleado.has(), Persona.socio.has()))

    if normalized_filters["dni"]:
        query = query.filter(Persona.dni == normalized_filters["dni"])

    if normalized_filters["email"]:
        query = query.filter(db.func.lower(Persona.email) == normalized_filters["email"])

    if normalized_filters["nombre"]:
        nombre_completo = db.func.lower(Persona.nombre + " " + Persona.apellido)
        query = query.filter(nombre_completo.contains(normalized_filters["nombre"]))

    users = query.order_by(Persona.apellido, Persona.nombre, Persona.persona_id).all()

    return {
        "status": "ok",
        "users": [_serializar_usuario(persona) for persona in users],
        "filters": normalized_filters,
    }, 200


def obtener_usuario_modificable(persona_id):
    persona = _obtener_persona_modificable(persona_id)
    if persona is None:
        return _not_found_response()

    return {"status": "ok", "user": _serializar_usuario(persona)}, 200


def actualizar_usuario(persona_id, payload):
    persona = _obtener_persona_modificable(persona_id)
    if persona is None:
        return _not_found_response()

    normalized_payload, errors = _validar_payload_actualizacion(persona, payload)
    if errors:
        return {"status": "validation_error", "errors": errors}, 400

    existing_email_owner = Persona.query.filter(
        db.func.lower(Persona.email) == normalized_payload["email"],
        Persona.persona_id != persona.persona_id,
    ).first()
    if existing_email_owner is not None:
        return _validation_error(
            "email",
            "El email ya se encuentra registrado en el sistema.",
        ), 400

    persona.email = normalized_payload["email"]
    persona.nombre = normalized_payload["nombre"]
    persona.apellido = normalized_payload["apellido"]
    persona.telefono = normalized_payload["telefono"]
    persona.calle = normalized_payload["calle"]
    persona.numero_puerta = normalized_payload["numero_puerta"]
    persona.codigo_postal = normalized_payload["codigo_postal"]

    try:
        db.session.commit()
    except IntegrityError as error:
        db.session.rollback()
        return _integrity_error_response(error)

    return {
        "status": "updated",
        "message": USER_UPDATED_MESSAGE,
        "redirect_to": "/inicio",
        "user": _serializar_usuario(persona),
    }, 200


def _validar_payload_actualizacion(persona, payload):
    payload_with_current_dni = {**(payload or {})}

    if not str(payload_with_current_dni.get("dni") or "").strip():
        payload_with_current_dni["dni"] = persona.dni

    normalized_payload, errors = validar_payload_registro_empleado(payload_with_current_dni)

    if normalized_payload["dni"] != persona.dni:
        errors["dni"] = "El DNI no puede modificarse."

    normalized_payload["dni"] = persona.dni
    normalized_payload["email"] = normalizar_email(normalized_payload["email"])

    return normalized_payload, errors


def _obtener_persona_modificable(persona_id):
    persona = db.session.get(Persona, persona_id)

    if persona is None:
        return None

    if persona.empleado is None and persona.socio is None:
        return None

    return persona


def _serializar_usuario(persona):
    return {
        "persona_id": persona.persona_id,
        "dni": persona.dni,
        "email": persona.email,
        "nombre": persona.nombre,
        "nombre_completo": persona.nombre_completo,
        "apellido": persona.apellido,
        "telefono": persona.telefono,
        "calle": persona.calle,
        "numero_puerta": persona.numero_puerta,
        "codigo_postal": persona.codigo_postal,
        "estado": persona.estado,
        "roles": _roles_modificables(persona),
    }


def _roles_modificables(persona):
    roles = []

    if persona.empleado is not None:
        roles.append("empleado")

    if persona.socio is not None:
        roles.append("socio")

    return roles


def _normalizar_filtros_listado(filters):
    filters = filters or {}

    return {
        "dni": str(filters.get("dni") or "").strip(),
        "email": normalizar_email(filters.get("email") or ""),
        "nombre": str(filters.get("nombre") or "").strip().lower(),
    }


def _not_found_response():
    return {
        "status": "error",
        "message": "No se encontró un socio o empleado disponible para modificar.",
    }, 404


def _validation_error(field, message):
    return {"status": "validation_error", "errors": {field: message}}


def _integrity_error_response(error):
    detail = str(getattr(error, "orig", error)).lower()

    if "dni" in detail:
        return _validation_error(
            "dni",
            "El DNI ya se encuentra registrado en el sistema.",
        ), 400

    if "email" in detail:
        return _validation_error(
            "email",
            "El email ya se encuentra registrado en el sistema.",
        ), 400

    return {
        "status": "error",
        "message": "No se pudo actualizar el usuario por un conflicto de datos.",
    }, 409

from src.core.models.reserva import Reserva
from src.core.models.clase import Clase
from src.core.models.pago import Pago
from src.core.services.reservas import _ofrecer_cupo_a_primero, _reintegrar_mercadopago, RESERVA_ESTADOS_OCUPAN_CUPO
from datetime import datetime, timezone

def _now():
    return datetime.now(timezone.utc)

def bloquear_usuario_service(persona_id, motivo, devolver_dinero=False):
    persona = _obtener_persona_modificable(persona_id)
    if persona is None:
        return _not_found_response()
        
    if not motivo:
        return {"status": "validation_error", "errors": {"motivo": "Debe ingresar un motivo de bloqueo para poder bloquear al usuario"}}, 400

    persona.estado = "bloqueado"
    persona.motivo_bloqueo = motivo

    reservas = Reserva.query.filter_by(socio_id=persona_id).filter(Reserva.estado.in_(RESERVA_ESTADOS_OCUPAN_CUPO)).all()

    for reserva in reservas:
        reserva.estado = "cancelada"
        reserva.cancelada_en = _now()
        db.session.flush()
        
        clase = db.session.get(Clase, reserva.clase_id)
        if clase is not None:
            _ofrecer_cupo_a_primero(clase)

        if devolver_dinero:
            pago = Pago.query.filter_by(reserva_id=reserva.reserva_id).order_by(Pago.pago_id.desc()).first()
            if pago and getattr(pago, "estado", "") in {"aprobado", "approved"}:
                _reintegrar_mercadopago(pago, pago.monto_pagado)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return {"status": "error", "message": str(e)}, 500

    return {
        "status": "ok",
        "message": f"El usuario {persona.nombre} {persona.apellido} ha sido bloqueado exitosamente.",
        "user": _serializar_usuario(persona)
    }, 200

def desbloquear_usuario_service(persona_id):
    persona = _obtener_persona_modificable(persona_id)
    if persona is None:
        return _not_found_response()

    persona.estado = "activo"
    persona.motivo_bloqueo = None
    
    if persona.socio is not None:
        persona.socio.descuento_bloqueado_hasta = None

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return {"status": "error", "message": str(e)}, 500

    return {
        "status": "ok",
        "message": "Usuario desbloqueado.",
        "user": _serializar_usuario(persona)
    }, 200
