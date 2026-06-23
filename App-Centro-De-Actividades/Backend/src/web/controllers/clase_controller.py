from flask import Blueprint, jsonify, request
from flask_login import current_user

from src.core.database import db
from src.core.models.clase import Clase
from src.core.models.reserva import Reserva
from src.core.services.clase_service import (
    validar_payload_clase,
    validar_payload_actualizar_clase,
    crear_clase_completa,
    obtener_clases,
    obtener_detalle_clase_con_socios,
    actualizar_clase,
    cancelar_clase,
)

clase_bp = Blueprint("clase", __name__, url_prefix="/api/clase")
ESTADOS_OCUPAN_CUPO = ("pendiente_pago", "confirmada")


@clase_bp.post("/crear")
def crear_clase():
    payload = request.get_json(silent=True) or {}
    normalized_payload, errors = validar_payload_clase(payload)

    if errors:
        return jsonify({"status": "validation_error", "errors": errors}), 400

    body, status_code = crear_clase_completa(normalized_payload)
    return jsonify(body), status_code


@clase_bp.get("/lista")
def listar_clases():
    actividad = (request.args.get("actividad") or "").strip()
    fecha = (request.args.get("fecha") or "").strip()
    horario = (request.args.get("horario") or "").strip()
    clases = obtener_clases(actividad, fecha, horario)
    cupos_ocupados = _obtener_cupos_ocupados(clases)
    clases_reservadas = _obtener_clases_reservadas_por_socio(clases)
    clases_data = [
        {
            "clase_id": clase.clase_id,
            "actividad": clase.actividad.value,
            "fecha": clase.fecha.strftime("%Y-%m-%d"),
            "horario_inicio": clase.horario_inicio.strftime("%H:%M"),
            "horario_fin": clase.horario_fin.strftime("%H:%M"),
            "cancha": clase.cancha,
            "nivel": clase.nivel.value,
            "cupos": clase.cupos,
            "cupos_ocupados": cupos_ocupados.get(clase.clase_id, 0),
            "precio": float(clase.precio) if clase.precio is not None else None,
            "tipo_clase": clase.tipo_clase.value,
            "profesor_id": clase.profesor_id,
            "profesor_nombre": clase.profesor.nombre if clase.profesor else None,
            "ya_reservado": clase.clase_id in clases_reservadas,
        }
        for clase in clases
    ]

    return jsonify(clases_data), 200


@clase_bp.put("/actualizar/<int:clase_id>")
def actualizar_clase_controller(clase_id):
    payload = request.get_json(silent=True) or {}
    
    normalized_payload, errors = validar_payload_actualizar_clase(payload)
    print("Payload recibido despues de validar:", normalized_payload, errors)   
    if errors:
        return jsonify({"status": "validation_error", "errors": errors}), 400

    body, status_code = actualizar_clase(clase_id, normalized_payload)
    return jsonify(body), status_code


def _obtener_cupos_ocupados(clases):
    clase_ids = [clase.clase_id for clase in clases]
    if not clase_ids:
        return {}

    rows = (
        db.session.query(Reserva.clase_id, db.func.count(Reserva.reserva_id))
        .filter(Reserva.clase_id.in_(clase_ids))
        .filter(Reserva.estado.in_(ESTADOS_OCUPAN_CUPO))
        .group_by(Reserva.clase_id)
        .all()
    )

    return {clase_id: int(total) for clase_id, total in rows}


def _obtener_clases_reservadas_por_socio(clases):
    if not current_user.is_authenticated or getattr(current_user, "role", None) != "socio":
        return set()

    clase_ids = [clase.clase_id for clase in clases]
    if not clase_ids:
        return set()

    rows = (
        db.session.query(Reserva.clase_id)
        .filter(Reserva.clase_id.in_(clase_ids))
        .filter(Reserva.socio_id == current_user.persona_id)
        .filter(Reserva.estado == "confirmada")
        .all()
    )

    return {clase_id for (clase_id,) in rows}


@clase_bp.get("/<int:clase_id>/detalle")
def obtener_detalle_clase(clase_id):
    """Obtiene el detalle de una clase con los socios registrados y su estado de asistencia."""
    dni = (request.args.get("dni") or "").strip()
    dni_filter = dni if dni else None
    clase_data, status_code = obtener_detalle_clase_con_socios(clase_id, dni_filter)

    if status_code == 404:
        return jsonify({"status": "error", "message": "La clase no fue encontrada."}), 404

    return jsonify(clase_data), status_code


@clase_bp.post('/cancelar/<int:clase_id>')
def cancelar_clase_controller(clase_id):
    body, status_code = cancelar_clase(clase_id)
    return jsonify(body), status_code
