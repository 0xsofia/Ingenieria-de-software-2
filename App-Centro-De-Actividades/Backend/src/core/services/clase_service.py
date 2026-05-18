import json
import re
from pathlib import Path
from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError
 
from src.core.database import db
from src.core.models.clase import Clase
from src.core.models.profesor import Profesor
from src.core.enums.clase_enum import ActividadEnum, NivelEnum, TipoClaseEnum

ACTIVIDADES_VALIDAS = {e.value for e in ActividadEnum}
NIVELES_VALIDOS = {e.value for e in NivelEnum}



def validar_payload_clase(payload):
    """Valida los datos de una clase con estructura de registro robusto."""
    normalized_payload = {
        "actividad": (payload.get("actividad") or "").strip(),
        "fecha": payload.get("fecha"),
        "horario_inicio": payload.get("horario_inicio"),
        "cancha": (payload.get("cancha") or "").strip(),
        "nivel": (payload.get("nivel") or "").strip(),
        "cupos": payload.get("cupos"),
        "profesor_id": payload.get("profesor_id"),
    }
    errors = {}

    # Validar actividad
    if not normalized_payload["actividad"]:
        errors["actividad"] = "La actividad es obligatoria."
    elif normalized_payload["actividad"] not in ACTIVIDADES_VALIDAS:
        errors["actividad"] = f"La actividad debe ser una de: {', '.join(ACTIVIDADES_VALIDAS)}"

    # Validar fecha
    if not normalized_payload["fecha"]:
        errors["fecha"] = "La fecha es obligatoria."
    else:
        try:
            fecha_obj = datetime.strptime(normalized_payload["fecha"], "%Y-%m-%d").date()
            if fecha_obj < datetime.now().date():
                errors["fecha"] = "La fecha no puede ser en el pasado."
        except ValueError:
            errors["fecha"] = "La fecha debe tener formato YYYY-MM-DD."

    # Validar horario_inicio
    if not normalized_payload["horario_inicio"]:
        errors["horario_inicio"] = "El horario de inicio es obligatorio."
    else:
        try:
            datetime.strptime(f"{normalized_payload["horario_inicio"]:02d}:00", "%H:%M").time()
        except ValueError:
            errors["horario_inicio"] = "El horario debe tener formato HH:MM."

    # Validar cancha
    if not normalized_payload["cancha"]:
        errors["cancha"] = "La cancha es obligatoria."
    elif len(normalized_payload["cancha"]) > 100:
        errors["cancha"] = "La cancha no puede exceder 100 caracteres."

    # Validar nivel
    if not normalized_payload["nivel"]:
        errors["nivel"] = "El nivel es obligatorio."
    elif normalized_payload["nivel"] not in NIVELES_VALIDOS:
        errors["nivel"] = f"El nivel debe ser uno de: {', '.join(NIVELES_VALIDOS)}"

    # Validar cupos
    if normalized_payload["cupos"] is None:
        errors["cupos"] = "Los cupos son obligatorios."
    else:
        try:
            cupos_int = int(normalized_payload["cupos"])
            if cupos_int < 1:
                errors["cupos"] = "Los cupos deben ser al menos 1."
        except (ValueError, TypeError):
            errors["cupos"] = "Los cupos deben ser un número válido."

    # Validar profesor_id
    if not normalized_payload["profesor_id"]:
        errors["profesor_id"] = "El profesor es obligatorio."
    else:
        try:
            profesor_id = int(normalized_payload["profesor_id"])
            profesor = Profesor.query.get(profesor_id)
            if not profesor:
                errors["profesor_id"] = "El profesor seleccionado no existe."
        except (ValueError, TypeError):
            errors["profesor_id"] = "El profesor_id debe ser un número válido."

    return normalized_payload, errors


def crear_clase_completa(payload):
    """Crea una clase con validación completa."""
    # Verificar duplicados
    try:
        fecha_obj = datetime.strptime(payload["fecha"], "%Y-%m-%d").date()
        horario_obj = datetime.strptime(f"{payload["horario_inicio"]:02d}:00", "%H:%M").time()
        
        clase_existente = Clase.query.filter_by(
            profesor_id=int(payload["profesor_id"]),
            fecha=fecha_obj,
            horario_inicio=horario_obj, 
        ).first()
        
        if clase_existente:
            return (
                {
                    "status":"error", 
                    "message": "No se puede registrar la clase, el profesor tiene superposición horaria con otra clase"
                },
                400,
            )
    except Exception as e:
        return (
            {
                "status": "error",
                "message": "Error al procesar los datos de la clase."
            },
            400,
        )

    # Crear tipo de clase basado en cupos
    cupos_int = int(payload["cupos"])
    tipo_clase = TipoClaseEnum.PARTICULAR if cupos_int == 1 else TipoClaseEnum.GRUPAL

    # Calcular horario_fin (1 hora después del inicio)
    horario_fin = (datetime.combine(fecha_obj, horario_obj) + timedelta(hours=1)).time()

    try:
        nueva_clase = Clase(
            actividad=ActividadEnum(payload["actividad"]),
            fecha=fecha_obj,
            horario_inicio=horario_obj,
            horario_fin=horario_fin,
            cancha=payload["cancha"],
            nivel=NivelEnum(payload["nivel"]),
            cupos=cupos_int,
            tipo_clase=tipo_clase,
            profesor_id=int(payload["profesor_id"])
        )

        db.session.add(nueva_clase)
        db.session.flush()
        db.session.commit()
    except IntegrityError as error:
        db.session.rollback()
        return _integrity_error_response(error)

    return {
        "status": "created",
        "message": "La clase ha sido creada con éxito.",
        "redirect_to": "/clases",
        "clase_id": nueva_clase.clase_id
    }, 201


def obtener_clases(actividad=None):
    """Obtiene las clases con un filtro opcional por actividad."""
    query = Clase.query

    if actividad:
        try:
            actividad_enum = ActividadEnum(actividad)
            query = query.filter(Clase.actividad == actividad_enum)
        except ValueError:
            return []

    return query.order_by(Clase.fecha, Clase.horario_inicio).all()


def _validation_error(field, message):
    return {"status": "validation_error", "errors": {field: message}}


def _integrity_error_response(error):
    detail = str(getattr(error, "orig", error)).lower()

    if "profesor_id" in detail:
        return (
            _validation_error(
                "profesor_id", "El profesor seleccionado no es válido."
            ),
            400,
        )

    return {
        "status": "error",
        "message": "No se pudo completar el registro de la clase por un conflicto de datos.",
    }, 409
