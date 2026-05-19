from flask import Blueprint, jsonify, request

from src.core.models.clase import Clase
from src.core.services.clase_service import (
    validar_payload_clase,
    crear_clase_completa,
    obtener_clases,
)

clase_bp = Blueprint("clase", __name__, url_prefix="/api/clase")


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
            "precio": float(clase.precio) if clase.precio is not None else None,
            "tipo_clase": clase.tipo_clase.value,
            "profesor_id": clase.profesor_id,
            "profesor_nombre": clase.profesor.nombre if clase.profesor else None,
        }
        for clase in clases
    ]

    return jsonify(clases_data), 200

