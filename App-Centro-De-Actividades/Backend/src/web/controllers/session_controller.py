from flask import Blueprint, jsonify

from src.core.services.iniciar_sesion import cerrar_sesion

session_bp = Blueprint('session', __name__, url_prefix='/api/session')

@session_bp.post("/logout")
def logout():
    body, status_code = cerrar_sesion()
    return jsonify(body), status_code
