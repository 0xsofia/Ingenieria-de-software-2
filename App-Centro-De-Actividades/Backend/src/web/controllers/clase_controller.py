from flask import Blueprint, jsonify, request

from src.core.services.clase_service import validar_payload_clase, crear_clase_completa

clase_bp = Blueprint("clase", __name__, url_prefix="/api/clase")


@clase_bp.post("/crear")
def crear_clase():
    payload = request.get_json(silent=True) or {}
    normalized_payload, errors = validar_payload_clase(payload)

    if errors:
        return jsonify({"status": "validation_error", "errors": errors}), 400

    body, status_code = crear_clase_completa(normalized_payload)
    return jsonify(body), status_code
