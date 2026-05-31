from flask import Blueprint, jsonify, request

from src.core.services.reservas import (
    obtener_oferta_desde_token,
    confirmar_turno_desde_token,
)


confirmaciones_bp = Blueprint("confirmaciones", __name__, url_prefix="/api")


@confirmaciones_bp.get('/confirmaciones/turno/<token>')
def obtener_confirmacion(token):
    """Obtiene la información de la oferta sin confirmarla."""
    if not token or len(token) != 32:
        return jsonify({
            "status": "error",
            "message": "Token inválido.",
        }), 400
    
    body, status_code = obtener_oferta_desde_token(token)
    return jsonify(body), status_code


@confirmaciones_bp.post('/confirmaciones/turno/<token>/confirmar')
def confirmar_desde_token(token):
    """Confirma el turno desde el link de Telegram."""
    if not token or len(token) != 32:
        return jsonify({
            "status": "error",
            "message": "Token inválido.",
        }), 400
    
    body, status_code = confirmar_turno_desde_token(token)
    return jsonify(body), status_code
