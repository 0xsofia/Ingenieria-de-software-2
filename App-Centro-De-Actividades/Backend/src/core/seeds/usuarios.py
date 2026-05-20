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

DEFAULT_PASSWORD = "123456."

# Agregar permisos por rol extendiendo las listas de cada entrada.
ROLE_PERMISSIONS = {
    "administrador": [],
    "empleado": [],
    "socio": [],
}

USERS_TO_SEED = [
    {
        "email": "admin@centro.test",
        "dni": "30000001",
        "nombre": "Admin",
        "apellido": "Centro",
        "telefono": "2215003001",
        "calle": "Calle 1",
        "numero_puerta": "100",
        "codigo_postal": "1900",
        "intereses": "",
        "roles": ["administrador"],
    },
    {
        "email": "empleado@centro.test",
        "dni": "30000002",
        "nombre": "Empleada",
        "apellido": "Mostrador",
        "telefono": "2215003002",
        "calle": "Calle 2",
        "numero_puerta": "200",
        "codigo_postal": "1900",
        "intereses": "",
        "roles": ["empleado", "socio"],
    },
    {
        "email": "socio@centro.test",
        "dni": "30000003",
        "nombre": "Socia",
        "apellido": "Activa",
        "telefono": "2215003003",
        "calle": "Calle 3",
        "numero_puerta": "300",
        "codigo_postal": "1900",
        "intereses": "",
        "roles": ["socio"],
    },
    {
        "email": "dni.duplicado@example.com",
        "dni": "22222222",
        "nombre": "Dni",
        "apellido": "Duplicado",
        "telefono": "2215003004",
        "calle": "Calle 4",
        "numero_puerta": "400",
        "codigo_postal": "1900",
        "intereses": "",
        "roles": ["socio"],
    },
    {
        "email": "example@gmail.com",
        "dni": "55555555",
        "nombre": "Luiz",
        "apellido": "Petri",
        "telefono": "2217776633",
        "calle": "59",
        "numero_puerta": "326",
        "codigo_postal": "1900",
        "intereses": "",
        "roles": ["socio"],
    },
    {
        "email": "example2@gmail.com",
        "dni": "77777777",
        "nombre": "Lucas",
        "apellido": "Petri",
        "telefono": "2217776634",
        "calle": "60",
        "numero_puerta": "327",
        "codigo_postal": "1900",
        "intereses": "",
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
    persona = _find_persona_for_seed(email=email, dni=user_data["dni"])

    if persona is None:
        persona = Persona(
            dni=user_data["dni"],
            email=email,
            nombre=user_data["nombre"],
            apellido=user_data["apellido"],
            telefono=user_data["telefono"],
            calle=user_data["calle"],
            numero_puerta=user_data["numero_puerta"],
            codigo_postal=user_data["codigo_postal"],
            estado="activo",
            intereses=_normalize_optional_text(user_data.get("intereses", "")),
            password_hash=_hash_password(DEFAULT_PASSWORD),
        )
        db.session.add(persona)
        db.session.flush()
        return persona

    persona.dni = user_data["dni"]
    persona.email = email
    persona.nombre = user_data["nombre"]
    persona.apellido = user_data["apellido"]
    persona.telefono = user_data["telefono"]
    persona.calle = user_data["calle"]
    persona.numero_puerta = user_data["numero_puerta"]
    persona.codigo_postal = user_data["codigo_postal"]
    persona.estado = "activo"
    persona.intereses = _normalize_optional_text(user_data.get("intereses", ""))
    persona.password_hash = _hash_password(DEFAULT_PASSWORD)
    db.session.flush()
    return persona


def _find_persona_for_seed(email, dni):
    persona = Persona.query.filter_by(email=email).first()
    if persona is not None:
        return persona

    return Persona.query.filter_by(dni=dni.strip()).first()


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


def _normalize_optional_text(value):
    return (value or "").strip()
