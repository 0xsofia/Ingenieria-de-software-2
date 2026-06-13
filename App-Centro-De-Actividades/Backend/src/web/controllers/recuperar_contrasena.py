import re
from flask import Blueprint, jsonify, request
from src.core.services.recuperar_contrasena import solicitar_recuperacion

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

recuperar_contrasena_bp = Blueprint("recuperar_contrasena", __name__, url_prefix="/api/recuperar-contrasena")

@recuperar_contrasena_bp.post("")
def solicitar():
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip().lower()
    
    if not email:
        return jsonify({"status": "validation_error", "errors": {"email": "El email es obligatorio."}}), 400
    elif not EMAIL_PATTERN.match(email):
        return jsonify({"status": "validation_error", "errors": {"email": "Ingresá un email válido."}}), 400
        
    body, status_code = solicitar_recuperacion(email)
    return jsonify(body), status_code
