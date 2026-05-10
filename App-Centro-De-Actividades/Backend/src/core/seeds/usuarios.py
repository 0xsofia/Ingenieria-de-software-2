from src.core.bcrypt_and_session import bcrypt
from src.core.database import db
from src.core.models.persona import (
    Empleado,
    Permiso,
    Persona,
    PersonaRolPuente,
    Rol,
    RolPermisoPuente,
    Socio,
)

DEFAULT_PASSWORD = "1234"

# Agregar permisos por rol extendiendo las listas de cada entrada.
ROLE_PERMISSIONS = {
    "administrador": [],
    "empleado": [],
    "socio": [],
}

USERS_TO_SEED = [
    {
        "email": "admin@centro.test",
        "nombre": "Admin",
        "apellido": "Centro",
        "roles": ["administrador"],
    },
    {
        "email": "empleado@centro.test",
        "nombre": "Empleada",
        "apellido": "Mostrador",
        "roles": ["empleado"],
    },
    {
        "email": "socio@centro.test",
        "nombre": "Socia",
        "apellido": "Activa",
        "roles": ["socio"],
    },
]


def seed_usuarios():
    for role_name, permission_codes in ROLE_PERMISSIONS.items():
        role = _get_or_create_role(role_name)
        _ensure_role_permissions(role, permission_codes)

    for user_data in USERS_TO_SEED:
        persona = _get_or_create_persona(user_data)
        _ensure_role_assignments(persona, user_data["roles"])
        _ensure_role_entities(persona, user_data["roles"])

    db.session.commit()


def _get_or_create_persona(user_data):
    email = user_data["email"].strip().lower()
    persona = Persona.query.filter_by(email=email).first()

    if persona is None:
        persona = Persona(
            email=email,
            nombre=user_data["nombre"],
            apellido=user_data["apellido"],
            estado="activo",
            password_hash=_hash_password(DEFAULT_PASSWORD),
        )
        db.session.add(persona)
        db.session.flush()
        return persona

    persona.nombre = user_data["nombre"]
    persona.apellido = user_data["apellido"]
    persona.estado = "activo"
    persona.password_hash = _hash_password(DEFAULT_PASSWORD)
    db.session.flush()
    return persona


def _get_or_create_role(role_name):
    normalized_name = _normalize_name(role_name)
    role = Rol.query.filter_by(nombre=normalized_name).first()

    if role is None:
        role = Rol(
            nombre=normalized_name,
            descripcion=f"Rol base de login para {normalized_name}.",
        )
        db.session.add(role)
        db.session.flush()

    return role


def _ensure_role_permissions(role, permission_codes):
    existing_codes = {permiso.codigo for permiso in role.permisos}

    for permission_code in permission_codes:
        normalized_code = permission_code.strip().lower()
        permiso = Permiso.query.filter_by(codigo=normalized_code).first()

        if permiso is None:
            permiso = Permiso(
                codigo=normalized_code,
                descripcion=f"Permiso seed {normalized_code}.",
            )
            db.session.add(permiso)
            db.session.flush()

        if normalized_code not in existing_codes:
            db.session.add(
                RolPermisoPuente(rol_id=role.rol_id, permiso_id=permiso.permiso_id)
            )
            existing_codes.add(normalized_code)


def _ensure_role_assignments(persona, role_names):
    current_role_ids = {assignment.rol_id for assignment in persona.persona_roles}

    for role_name in role_names:
        role = _get_or_create_role(role_name)
        if role.rol_id not in current_role_ids:
            db.session.add(
                PersonaRolPuente(persona_id=persona.persona_id, rol_id=role.rol_id)
            )
            current_role_ids.add(role.rol_id)


def _ensure_role_entities(persona, role_names):
    normalized_roles = {_normalize_name(role_name) for role_name in role_names}

    if "empleado" in normalized_roles and persona.empleado is None:
        db.session.add(Empleado(persona_id=persona.persona_id))

    if "socio" in normalized_roles and persona.socio is None:
        db.session.add(Socio(persona_id=persona.persona_id))


def _hash_password(password):
    return bcrypt.generate_password_hash(password).decode("utf-8")


def _normalize_name(value):
    return value.strip().lower()
