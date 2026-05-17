from flask import Blueprint, jsonify, request
from flask_login import current_user

from src.core.services.registrarse import (
    registrar_empleado,
    validar_payload_registro_empleado,
)
from src.core.services.usuarios import (
    actualizar_usuario,
    obtener_usuario_modificable,
)

usuarios_bp = Blueprint("usuarios", __name__, url_prefix="/api/usuarios")


@usuarios_bp.post("/empleados")
def registrar_empleado_controller():
    admin_error = _require_admin()
    if admin_error is not None:
        return admin_error

    payload = request.get_json(silent=True) or {}
    normalized_payload, errors = validar_payload_registro_empleado(payload)

    if errors:
        return jsonify({"status": "validation_error", "errors": errors}), 400

    body, status_code = registrar_empleado(normalized_payload)
    return jsonify(body), status_code


@usuarios_bp.get("/<int:persona_id>")
def obtener_usuario_controller(persona_id):
    admin_error = _require_admin()
    if admin_error is not None:
        return admin_error

    body, status_code = obtener_usuario_modificable(persona_id)
    return jsonify(body), status_code


@usuarios_bp.put("/<int:persona_id>")
def actualizar_usuario_controller(persona_id):
    admin_error = _require_admin()
    if admin_error is not None:
        return admin_error

    payload = request.get_json(silent=True) or {}
    body, status_code = actualizar_usuario(persona_id, payload)
    return jsonify(body), status_code


def _require_admin():
    if not current_user.is_authenticated:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Debes iniciar sesión como administrador para acceder a esta funcionalidad.",
                }
            ),
            401,
        )

    if getattr(current_user, "role", "") != "administrador":
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Solo un administrador puede acceder a esta funcionalidad.",
                }
            ),
            403,
        )

    return None
