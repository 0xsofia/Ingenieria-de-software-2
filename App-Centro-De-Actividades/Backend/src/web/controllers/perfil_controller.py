from flask import Blueprint, jsonify, request

from src.core.services.perfil import actualizar_perfil, obtener_perfil_actual

perfil_bp = Blueprint("perfil", __name__, url_prefix="/api/perfil")


@perfil_bp.get("/me")
def get_perfil():
    body, status_code = obtener_perfil_actual()
    return jsonify(body), status_code


@perfil_bp.put("/me")
def update_perfil():
    payload = request.get_json(silent=True) or {}
    body, status_code = actualizar_perfil(payload)
    return jsonify(body), status_code
