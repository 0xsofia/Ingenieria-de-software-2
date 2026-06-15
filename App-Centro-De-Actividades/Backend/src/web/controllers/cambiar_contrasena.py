from flask import Blueprint, jsonify, request
from flask_login import current_user
from src.core.services.cambiar_contrasena import cambiar_contrasena
from src.core.models.persona import Persona

cambiar_contrasena_bp = Blueprint(
    "cambiar_contrasena", __name__, url_prefix="/api/cambiar-contrasena"
)


@cambiar_contrasena_bp.get("/<token>")
def validar_token(token):
    persona = Persona.query.filter_by(token_recuperacion=token).first()
    if not persona:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Este email de recuperacion ya ha sido utilizado, recupere su contraseña nuevamente",
                }
            ),
            400,
        )
    return jsonify({"status": "success", "message": "Token válido"}), 200


@cambiar_contrasena_bp.post("")
def cambiar():
    payload = request.get_json(silent=True) or {}

    token = payload.get("token")
    current_password = payload.get("current_password")
    new_password = payload.get("new_password")
    repeat_password = payload.get("repeat_password")

    if not new_password or not repeat_password:
        return (
            jsonify(
                {
                    "status": "validation_error",
                    "errors": {"new_password": "La nueva contraseña es obligatoria."},
                }
            ),
            400,
        )

    if len(new_password) < 6 or len(new_password) > 12:
        return (
            jsonify(
                {
                    "status": "validation_error",
                    "errors": {
                        "new_password": "La contraseña debe tener entre 6 a 12 caracteres."
                    },
                }
            ),
            400,
        )

    if new_password != repeat_password:
        return (
            jsonify(
                {
                    "status": "validation_error",
                    "errors": {
                        "repeat_password": "La contraseña ingresada no coincide con la ingresada en Contraseña nueva"
                    },
                }
            ),
            400,
        )

    email = None
    if not token:
        # If no token, user must be authenticated
        if not current_user.is_authenticated:
            return jsonify({"status": "error", "message": "No autorizado."}), 401
        email = current_user.email
        if not current_password:
            return (
                jsonify(
                    {
                        "status": "validation_error",
                        "errors": {
                            "current_password": "La contraseña actual es obligatoria."
                        },
                    }
                ),
                400,
            )

    body, status_code = cambiar_contrasena(email, current_password, new_password, token)
    return jsonify(body), status_code
