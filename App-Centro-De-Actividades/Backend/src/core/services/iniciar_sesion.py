from flask import session as flask_session
from flask_login import UserMixin, current_user, login_user, logout_user

from src.core.bcrypt_and_session import bcrypt, login_manager
from src.core.database import db
from src.core.models.credito import Credito
from src.core.models.persona import Persona, Rol

PENDING_LOGIN_KEY = "pending_login"

ROLE_LABELS = {
    "administrador": "Administrador",
    "empleado": "Empleado",
    "socio": "Socio",
}
LOGIN_ROLE_NAMES = {"administrador", "empleado", "socio"}


class AuthenticatedUser(UserMixin):
    def __init__(self, persona, role):
        normalized_role = _normalizar_rol(role.nombre)

        self.persona_id = persona.persona_id
        self.email = persona.email
        self.nombre = persona.nombre
        self.apellido = persona.apellido
        self.dni = persona.dni
        self.intereses = getattr(persona, "intereses", "")
        self.descuento_bloqueado_hasta = (
            persona.socio.descuento_bloqueado_hasta if persona.socio is not None else None
        )
        self.creditos_disponibles = _contar_creditos_disponibles(persona.persona_id)
        self.display_name = persona.nombre_completo
        self.role_id = role.rol_id
        self.role = normalized_role
        self.role_label = ROLE_LABELS.get(normalized_role, role.nombre.title())
        self.permissions = role.permission_codes

    def get_id(self):
        return f"{self.persona_id}:{self.role_id}"


@login_manager.user_loader
def load_user(user_id):
    return _cargar_usuario_autenticado(user_id)


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
            "available_roles": [_normalizar_rol(rol.nombre) for rol in roles],
        }
        flask_session.permanent = True

        return {
            "status": "role_selection_required",
            "message": "Seleccioná cómo querés ingresar.",
            "available_roles": [_normalizar_rol(rol.nombre) for rol in roles],
            "identity": _build_identity(persona),
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
    if current_user.is_authenticated:
        return {"authenticated": True, "session": _build_auth_payload(current_user)}, 200

    pending_login = flask_session.get(PENDING_LOGIN_KEY)
    if pending_login is not None:
        persona = db.session.get(Persona, pending_login["persona_id"])
        if persona is None:
            _limpiar_estado_login()
            return {"authenticated": False}, 200

        return {
            "authenticated": False,
            "pending_role_selection": True,
            "available_roles": pending_login["available_roles"],
            "identity": _build_identity(persona),
        }, 200

    return {"authenticated": False}, 200


def autorizar_permiso(permission_code):
    if not current_user.is_authenticated:
        return {
            "status": "error",
            "message": "Debes iniciar sesión para validar permisos.",
        }, 401

    return {
        "status": "ok",
        "authorized": permission_code in current_user.permissions,
        "permission": permission_code,
        "role": current_user.role,
    }, 200


def cerrar_sesion():
    if not current_user.is_authenticated and flask_session.get(PENDING_LOGIN_KEY) is None:
        _limpiar_estado_login()
        return {
            "status": "logged_out",
            "message": "La sesión ya estaba cerrada.",
            "redirect_to": "/login",
        }, 200

    _limpiar_estado_login()

    return {
        "status": "logged_out",
        "message": "Sesión cerrada exitosamente.",
        "redirect_to": "/login",
    }, 200


def _finalizar_login(persona, role):
    _limpiar_estado_login()

    authenticated_user = AuthenticatedUser(persona, role)
    login_user(authenticated_user)
    flask_session.permanent = True

    auth_payload = _build_auth_payload(authenticated_user)

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


def _cargar_usuario_autenticado(user_id):
    persona_id, role_id = _parse_user_id(user_id)
    if persona_id is None or role_id is None:
        return None

    persona = db.session.get(Persona, persona_id)
    role = db.session.get(Rol, role_id)

    if persona is None or role is None:
        return None

    roles, error_response = _roles_disponibles(persona)
    if error_response is not None:
        return None

    if not any(assigned_role.rol_id == role.rol_id for assigned_role in roles):
        return None

    return AuthenticatedUser(persona, role)


def _build_auth_payload(authenticated_user):
    return {
        "persona_id": authenticated_user.persona_id,
        "email": authenticated_user.email,
        "nombre": authenticated_user.nombre,
        "apellido": authenticated_user.apellido,
        "dni": authenticated_user.dni,
        "intereses": authenticated_user.intereses,
        "display_name": authenticated_user.display_name,
        "role_id": authenticated_user.role_id,
        "role": authenticated_user.role,
        "role_label": authenticated_user.role_label,
        "permissions": authenticated_user.permissions,
        "descuento_bloqueado_hasta": (
            authenticated_user.descuento_bloqueado_hasta.isoformat()
            if authenticated_user.descuento_bloqueado_hasta is not None
            else None
        ),
        "creditos_disponibles": authenticated_user.creditos_disponibles,
    }


def _contar_creditos_disponibles(socio_id):
    return (
        Credito.query.filter_by(socio_id=socio_id)
        .filter(Credito.reserva_que_consume_id.is_(None))
        .filter(Credito.consumido_en.is_(None))
        .filter(db.func.lower(Credito.estado) == "disponible")
        .count()
    )


def _build_identity(persona):
    return {
        "email": persona.email,
        "display_name": persona.nombre_completo,
    }


def _parse_user_id(user_id):
    try:
        persona_id, role_id = user_id.split(":", maxsplit=1)
        return int(persona_id), int(role_id)
    except (AttributeError, TypeError, ValueError):
        return None, None



def _normalizar_rol(role_name):
    return (role_name or "").strip().lower()


def _limpiar_estado_login():
    logout_user()
    flask_session.pop(PENDING_LOGIN_KEY, None)


def _normalizar_email(email):
    return email.strip().lower()
