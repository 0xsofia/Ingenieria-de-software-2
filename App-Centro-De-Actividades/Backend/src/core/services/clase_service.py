import json
import re
from pathlib import Path
from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError
 
from src.core.database import db
from src.core.models.clase import Clase
from src.core.models.profesor import Profesor
from src.core.models.reserva import Reserva
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
        "precio": payload.get("precio"),
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
    if normalized_payload["horario_inicio"] is None or str(normalized_payload["horario_inicio"]).strip() == "":
        errors["horario_inicio"] = "El horario de inicio es obligatorio."
    else:
        try:
            horario_inicio_int = int(normalized_payload["horario_inicio"])
            if horario_inicio_int < 0 or horario_inicio_int > 23:
                errors["horario_inicio"] = "El horario debe estar entre 00:00 y 23:00."
            else:
                datetime.strptime(f"{horario_inicio_int:02d}:00", "%H:%M").time()
        except (TypeError, ValueError):
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

    precio_raw = normalized_payload.get("precio")
    if precio_raw is None or str(precio_raw).strip() == "":
        errors["precio"] = "El precio es obligatorio."
    else:
        try:
            precio_value = float(precio_raw)
            if precio_value < 0:
                errors["precio"] = "El precio no puede ser negativo."
            else:
                normalized_payload["precio"] = precio_value
        except (ValueError, TypeError):
            errors["precio"] = "El precio debe ser un número válido."

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

        # calcular fin de la nueva clase (1 hora)
        horario_fin = (datetime.combine(fecha_obj, horario_obj) + timedelta(hours=1)).time()

        # Buscar cualquier clase del mismo profesor en la misma fecha cuyo intervalo se solape
        clase_existente = Clase.query.filter(
            Clase.profesor_id == int(payload["profesor_id"]),
            Clase.fecha == fecha_obj,
            Clase.horario_inicio < horario_fin,
            Clase.horario_fin > horario_obj,
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
            precio=payload.get("precio"),
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


ESTADOS_OCUPAN_CUPO = ('confirmada', 'pendiente_pago')


def obtener_clases(actividad=None, fecha=None, horario=None):
    """Obtiene las clases con filtros opcionales por actividad, fecha y horario."""
    query = Clase.query

    if actividad:
        try:
            actividad_enum = ActividadEnum(actividad)
            query = query.filter(Clase.actividad == actividad_enum)
        except ValueError:
            return []

    if fecha:
        try:
            fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
            query = query.filter(Clase.fecha == fecha_obj)
        except ValueError:
            return []

    if horario:
        try:
            horario_obj = datetime.strptime(horario, "%H:%M").time()
            query = query.filter(Clase.horario_inicio == horario_obj)
        except ValueError:
            return []

    return query.order_by(Clase.fecha, Clase.horario_inicio).all()


def validar_payload_actualizar_clase(payload):
    """Valida los datos de una clase con estructura de registro robusto."""
    normalized_payload = {
        "actividad": (payload.get("actividad") or "").strip(),
        "fecha": payload.get("fecha"),
        "horario_inicio": payload.get("horario_inicio"),
        "cancha": (payload.get("cancha") or "").strip(),
        "nivel": (payload.get("nivel") or "").strip(),
        "cupos": payload.get("cupos"),
        "precio": payload.get("precio"),
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
    if normalized_payload["horario_inicio"] is None or str(normalized_payload["horario_inicio"]).strip() == "":
        errors["horario_inicio"] = "El horario de inicio es obligatorio."
    else:
        try:
            horario_inicio_int = int(normalized_payload["horario_inicio"])
            if horario_inicio_int < 0 or horario_inicio_int > 23:
                errors["horario_inicio"] = "El horario debe estar entre 00:00 y 23:00."
            else:
                datetime.strptime(f"{horario_inicio_int:02d}:00", "%H:%M").time()
        except (TypeError, ValueError):
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

    precio_raw = normalized_payload.get("precio")
    if precio_raw is None or str(precio_raw).strip() == "":
        errors["precio"] = "El precio es obligatorio."
    else:
        try:
            precio_value = float(precio_raw)
            if precio_value < 0:
                errors["precio"] = "El precio no puede ser negativo."
            else:
                normalized_payload["precio"] = precio_value
        except (ValueError, TypeError):
            errors["precio"] = "El precio debe ser un número válido."

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


def actualizar_clase(clase_id, payload):
    clase = Clase.query.get(clase_id)
    if not clase:
        return {
            "status": "error",
            "message": "La clase no fue encontrada.",
        }, 404

    cupos_ocupados = (
        Reserva.query.filter_by(clase_id=clase_id)
        .filter(Reserva.estado.in_(ESTADOS_OCUPAN_CUPO))
        .count()
    )

    payload_horario = payload.get('horario_inicio')
    if payload_horario is not None and str(payload_horario).strip() != '':
        horario_inicio_obj = datetime.strptime(f"{int(payload_horario):02d}:00", "%H:%M").time()
    else:
        horario_inicio_obj = clase.horario_inicio

    payload_fecha = payload.get('fecha')
    if payload_fecha is not None and str(payload_fecha).strip() != '':
        fecha_obj = datetime.strptime(payload_fecha, "%Y-%m-%d").date()
    else:
        fecha_obj = clase.fecha

    payload_profesor_id = payload.get('profesor_id')
    if payload_profesor_id is None or str(payload_profesor_id).strip() == '':
        profesor_id_value = clase.profesor_id
    else:
        try:
            profesor_id_value = int(payload_profesor_id)
        except (ValueError, TypeError):
            profesor_id_value = payload_profesor_id


    print("Clase en service ", clase.horario_inicio, clase.fecha, clase.profesor_id)
    print("payload en service", horario_inicio_obj, fecha_obj, payload['profesor_id']  )

    if cupos_ocupados > 0:
        if profesor_id_value != clase.profesor_id or horario_inicio_obj != clase.horario_inicio or fecha_obj != clase.fecha:
            return {
                "status": "error",
                "message": "No puede actualizarse la clase ya que tiene reservas activas y solo se pueden modificar los cupos.",
            }, 400

        if 'cupos' not in payload:
            return {
                "status": "error",
                "message": "Debe indicar la cantidad de cupos para actualizar la clase.",
            }, 400

        if int(payload['cupos']) < cupos_ocupados:
            return {
                "status": "error",
                "message": "La cantidad de cupos debe ser mayor o igual a la cantidad de reservas asociadas",
            }, 400

        clase.cupos = int(payload['cupos'])
        db.session.commit()

        return {
            "status": "success",
            "message": "La clase fue actualizada correctamente.",
        }, 200

    # calcular fin de la clase propuesta (1 hora)
    horario_fin_obj = (datetime.combine(fecha_obj, horario_inicio_obj) + timedelta(hours=1)).time()

    clase_existente = Clase.query.filter(
        Clase.profesor_id == int(payload['profesor_id']),
        Clase.fecha == fecha_obj,
        Clase.horario_inicio < horario_fin_obj,
        Clase.horario_fin > horario_inicio_obj,
        Clase.clase_id != clase_id,
    ).first()

    if clase_existente:
        return {
            "status": "error",
            "message": "No puede actualizarse la clase ya que el profesor tiene superposición horaria con otra clase",
        }, 400

    clase.actividad = ActividadEnum(payload['actividad'])
    clase.fecha = fecha_obj
    clase.horario_inicio = horario_inicio_obj
    clase.horario_fin = (datetime.combine(fecha_obj, horario_inicio_obj) + timedelta(hours=1)).time()
    clase.cancha = payload['cancha']
    clase.nivel = NivelEnum(payload['nivel'])
    clase.cupos = int(payload['cupos'])
    clase.precio = payload['precio']
    clase.profesor_id = int(payload['profesor_id'])

    db.session.commit()

    return {
        "status": "success",
        "message": "La clase fue actualizada correctamente.",
    }, 200

# def obtener_clases(actividad=None, fecha=None, horario=None):
#     """Obtiene las clases con filtros opcionales por actividad, fecha y horario."""
#     query = Clase.query
#     ahora = datetime.now()
#     fecha_actual = ahora.date()
#     hora_actual = ahora.time()

#     if actividad:
#         try:
#             actividad_enum = ActividadEnum(actividad)
#             query = query.filter(Clase.actividad == actividad_enum)
#         except ValueError:
#             return []

#     if fecha:
#         try:
#             fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
#             query = query.filter(Clase.fecha == fecha_obj)
#             if fecha_obj == fecha_actual and not horario:
#                 query = query.filter(Clase.horario_inicio >= hora_actual)

#         except ValueError:
#             return []
#     # else : 
#     #     fecha_actual = datetime.now().date()
#     #     query = query.filter(Clase.fecha >= fecha_actual)
#     else:
#         query = query.filter(
#             (Clase.fecha > fecha_actual) | 
#             ((Clase.fecha == fecha_actual) & (Clase.horario_inicio >= hora_actual))
#         )

#     if horario:
#         try:
#             horario_obj = datetime.strptime(horario, "%H:%M").time()
#             query = query.filter(Clase.horario_inicio == horario_obj)
#         except ValueError:
#             return []

#     # return query.order_by(Clase.fecha, Clase.horario_inicio).all()
#     # Para que ordene de fechas más cercanas
#     return query.order_by(Clase.fecha.asc(), Clase.horario_inicio.asc()).all()


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


def obtener_detalle_clase_con_socios(clase_id, dni=None):
    """Obtiene el detalle de una clase junto con los socios registrados y su estado de asistencia."""
    from src.core.models.persona import Persona
    from src.core.models.reserva import Reserva
    
    # Obtener la clase
    clase = Clase.query.get(clase_id)
    if not clase:
        return None, 404
    
    estados_validos = ['confirmada', 'pendiente_pago', 'asistio']
    query = Reserva.query.filter_by(clase_id=clase_id).filter(Reserva.estado.in_(estados_validos))

    if dni:
        dni_normalizado = str(dni).strip()
        query = query.join(Persona, Persona.persona_id == Reserva.socio_id).filter(Persona.dni == dni_normalizado)

    reservas = query.all()

    cupos_ocupados = (
        Reserva.query.filter_by(clase_id=clase_id)
        .filter(Reserva.estado.in_(estados_validos))
        .count()
    )
    
    # Construir lista de socios con su información de asistencia
    socios_data = []
    for reserva in reservas:
        persona = Persona.query.get(reserva.socio_id)
        if persona:
            socios_data.append({
                "reserva_id": reserva.reserva_id,
                "socio_id": reserva.socio_id,
                "nombre": persona.nombre,
                "apellido": persona.apellido,
                "nombre_completo": persona.nombre_completo,
                "email": persona.email,
                "telefono": persona.telefono,
                "dni": persona.dni,
                "estado_reserva": reserva.estado,
                "asistencia_registrada": reserva.estado == "asistio",
                "creada_en": reserva.creada_en.isoformat() if reserva.creada_en else None,
            })
    
    # Construir respuesta con datos de la clase
    clase_data = {
        "clase_id": clase.clase_id,
        "actividad": clase.actividad.value,
        "fecha": clase.fecha.strftime("%Y-%m-%d"),
        "horario_inicio": clase.horario_inicio.strftime("%H:%M"),
        "horario_fin": clase.horario_fin.strftime("%H:%M"),
        "cancha": clase.cancha,
        "nivel": clase.nivel.value,
        "cupos": clase.cupos,
        "cupos_ocupados": cupos_ocupados,
        "precio": float(clase.precio) if clase.precio is not None else None,
        "tipo_clase": clase.tipo_clase.value,
        "profesor_id": clase.profesor_id,
        "profesor_nombre": clase.profesor.nombre if clase.profesor else None,
        "socios": socios_data,
    }
    
    return clase_data, 200
