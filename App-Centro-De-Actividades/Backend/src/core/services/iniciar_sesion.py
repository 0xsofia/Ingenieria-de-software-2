from flask import session as flask_session

from src.core.bcrypt_and_session import bcrypt
from src.core.database import db
from src.core.models.persona import Persona, Rol

AUTH_SESSION_KEY = "auth_session"
PENDING_LOGIN_KEY = "pending_login"

ROLE_LABELS = {
    "administrador": "Administrador",
    "empleado": "Empleado",
    "socio": "Socio",
}
LOGIN_ROLE_NAMES = {"administrador", "empleado", "socio"}


def autenticar_credenciales(email, password):
    persona = Persona.query.filter_by(email=_normalizar_email(email)).first()

    _limpiar_estado_login()

    if persona is None:
        return {
            "status": "error",
            "message": "El email no se encuentra registrado en el sistema.",
        }, 401

    if not bcrypt.check_password_hash(persona.password_hash, password):
        return {
            "status": "error",
            "message": "La contraseña es incorrecta.",
        }, 401

    if (persona.estado or "activo").lower() != "activo":
        return {
            "status": "error",
            "message": "El usuario no puede iniciar sesión con su estado actual.",
        }, 403

    roles, error_response = _roles_disponibles(persona)
    if error_response is not None:
        return error_response

    if not roles:
        return {
            "status": "error",
            "message": "El usuario no tiene un rol habilitado para iniciar sesión.",
        }, 403

    if len(roles) > 1:
        flask_session[PENDING_LOGIN_KEY] = {
            "persona_id": persona.persona_id,
            "email": persona.email,
            "display_name": persona.nombre_completo,
            "available_roles": [_normalizar_rol(rol.nombre) for rol in roles],
        }
        flask_session.modified = True

        return {
            "status": "role_selection_required",
            "message": "Seleccioná cómo querés ingresar.",
            "available_roles": [_normalizar_rol(rol.nombre) for rol in roles],
            "identity": {
                "email": persona.email,
                "display_name": persona.nombre_completo,
            },
        }, 200

    return _finalizar_login(persona, roles[0])


def seleccionar_rol(role):
    pending_login = flask_session.get(PENDING_LOGIN_KEY)
    if pending_login is None:
        return {
            "status": "error",
            "message": "No hay un inicio de sesión pendiente para completar.",
        }, 400

    if role not in pending_login["available_roles"]:
        return {
            "status": "validation_error",
            "errors": {"role": "Seleccioná un rol válido para continuar."},
        }, 400

    persona = db.session.get(Persona, pending_login["persona_id"])
    if persona is None:
        _limpiar_estado_login()
        return {
            "status": "error",
            "message": "El usuario ya no está disponible para completar el inicio de sesión.",
        }, 404

    rol = Rol.query.filter(db.func.lower(Rol.nombre) == role).first()
    if rol is None:
        _limpiar_estado_login()
        return {
            "status": "error",
            "message": "El rol seleccionado ya no está disponible para iniciar sesión.",
        }, 404

    return _finalizar_login(persona, rol)


def obtener_estado_sesion():
    current_session = flask_session.get(AUTH_SESSION_KEY)
    if current_session is not None:
        session_payload = _reconstruir_sesion(current_session)
        if session_payload is None:
            _limpiar_estado_login()
            return {"authenticated": False}, 200

        flask_session[AUTH_SESSION_KEY] = session_payload
        flask_session.modified = True

        return {
            "authenticated": True,
            "session": session_payload,
        }, 200

    pending_login = flask_session.get(PENDING_LOGIN_KEY)
    if pending_login is not None:
        return {
            "authenticated": False,
            "pending_role_selection": True,
            "available_roles": pending_login["available_roles"],
            "identity": {
                "email": pending_login["email"],
                "display_name": pending_login["display_name"],
            },
        }, 200

    return {"authenticated": False}, 200


def autorizar_permiso(permission_code):
    current_session = flask_session.get(AUTH_SESSION_KEY)
    if current_session is None:
        return {
            "status": "error",
            "message": "Debes iniciar sesión para validar permisos.",
        }, 401

    session_payload = _reconstruir_sesion(current_session)
    if session_payload is None:
        _limpiar_estado_login()
        return {
            "status": "error",
            "message": "La sesión actual ya no es válida.",
        }, 401

    return {
        "status": "ok",
        "authorized": permission_code in session_payload["permissions"],
        "permission": permission_code,
        "role": session_payload["role"],
    }, 200


def _finalizar_login(persona, role):
    _limpiar_estado_login()

    auth_payload = _build_auth_payload(persona, role)
    flask_session[AUTH_SESSION_KEY] = auth_payload
    flask_session.modified = True

    return {
        "status": "authenticated",
        "message": f"Sesión iniciada como {auth_payload['role_label']}.",
        "session": auth_payload,
        "redirect_to": "/inicio",
    }, 200


def _roles_disponibles(persona):
    roles = {}
    invalid_roles = []

    for assigned_role in persona.roles:
        role_name = _normalizar_rol(assigned_role.nombre)
        if role_name not in LOGIN_ROLE_NAMES:
            continue

        if role_name == "administrador":
            roles[role_name] = assigned_role
            continue

        if role_name == "empleado" and persona.empleado is None:
            invalid_roles.append(role_name)
            continue

        if role_name == "socio" and persona.socio is None:
            invalid_roles.append(role_name)
            continue

        roles[role_name] = assigned_role

    if invalid_roles:
        return None, (
            {
                "status": "error",
                "message": "El usuario tiene roles con configuración incompleta para iniciar sesión.",
            },
            403,
        )

    if "administrador" in roles and len(roles) > 1:
        return None, (
            {
                "status": "error",
                "message": "El rol administrador debe iniciar sesión de forma exclusiva.",
            },
            409,
        )

    return list(roles.values()), None


def _reconstruir_sesion(current_session):
    persona = db.session.get(Persona, current_session.get("persona_id"))
    role = db.session.get(Rol, current_session.get("role_id"))

    if persona is None or role is None:
        return None

    roles, error_response = _roles_disponibles(persona)
    if error_response is not None:
        return None

    if not any(assigned_role.rol_id == role.rol_id for assigned_role in roles):
        return None

    return _build_auth_payload(persona, role)


def _build_auth_payload(persona, role):
    return {
        "persona_id": persona.persona_id,
        "email": persona.email,
        "display_name": persona.nombre_completo,
        "role_id": role.rol_id,
        "role": _normalizar_rol(role.nombre),
        "role_label": ROLE_LABELS.get(_normalizar_rol(role.nombre), role.nombre.title()),
        "permissions": role.permission_codes,
    }



def _normalizar_rol(role_name):
    return (role_name or "").strip().lower()


def _limpiar_estado_login():
    flask_session.pop(AUTH_SESSION_KEY, None)
    flask_session.pop(PENDING_LOGIN_KEY, None)


def _normalizar_email(email):
    return email.strip().lower()
