from flask import Blueprint, jsonify, request

from src.core.services.registrarse import registrar_socio, validar_payload_registro

registrarse_bp = Blueprint("registrarse", __name__, url_prefix="/api/registrarse")


@registrarse_bp.post("")
def registrarse_usuario():
    payload = request.get_json(silent=True) or {}
    normalized_payload, errors = validar_payload_registro(payload)

    if errors:
        return jsonify({"status": "validation_error", "errors": errors}), 400

    body, status_code = registrar_socio(normalized_payload)
    return jsonify(body), status_code
