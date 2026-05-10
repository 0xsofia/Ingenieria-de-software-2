import re

from flask import Blueprint, jsonify, request

from src.core.services.iniciar_sesion import (
    autenticar_credenciales,
    autorizar_permiso,
    obtener_estado_sesion,
    seleccionar_rol,
)

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
ROLE_OPTIONS = {"empleado", "socio"}

login_bp = Blueprint("login", __name__, url_prefix="/api/login")


@login_bp.post("")
def login():
    payload = request.get_json(silent=True) or {}
    errors = _validate_login_payload(payload)

    if errors:
        return jsonify({"status": "validation_error", "errors": errors}), 400

    body, status_code = autenticar_credenciales(payload["email"], payload["password"])
    return jsonify(body), status_code


@login_bp.post("/select-role")
def select_role():
    payload = request.get_json(silent=True) or {}
    role = (payload.get("role") or "").strip().lower()

    if role not in ROLE_OPTIONS:
        return (
            jsonify(
                {
                    "status": "validation_error",
                    "errors": {"role": "Seleccioná un rol válido para continuar."},
                }
            ),
            400,
        )

    body, status_code = seleccionar_rol(role)
    return jsonify(body), status_code


@login_bp.get("/session")
def get_session_state():
    body, status_code = obtener_estado_sesion()
    return jsonify(body), status_code


@login_bp.post("/authorize")
def authorize_permission():
    payload = request.get_json(silent=True) or {}
    permission = (payload.get("permission") or "").strip().lower()

    if not permission:
        return (
            jsonify(
                {
                    "status": "validation_error",
                    "errors": {"permission": "El permiso es obligatorio."},
                }
            ),
            400,
        )

    body, status_code = autorizar_permiso(permission)
    return jsonify(body), status_code


def _validate_login_payload(payload):
    errors = {}
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""

    if not email:
        errors["email"] = "El email es obligatorio."
    elif not EMAIL_PATTERN.match(email):
        errors["email"] = "Ingresá un email válido."

    if not password:
        errors["password"] = "La contraseña es obligatoria."
    elif len(password) < 4:
        errors["password"] = "La contraseña debe tener al menos 4 caracteres."
    elif len(password) > 128:
        errors["password"] = "La contraseña debe tener como máximo 128 caracteres."

    return errors
