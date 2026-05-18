from flask_login import current_user

from src.core.database import db
from src.core.models.persona import Persona


def _normalize_email(email):
    return (email or "").strip().lower()


def obtener_perfil_actual():
    if not current_user.is_authenticated:
        return {
            "status": "error",
            "message": "Debes iniciar sesión para ver el perfil.",
        }, 401

    persona = db.session.get(Persona, current_user.persona_id)
    if persona is None:
        return {
            "status": "error",
            "message": "No se encontró el perfil del usuario.",
        }, 404

    return {
        "status": "ok",
        "profile": {
            "persona_id": persona.persona_id,
            "email": persona.email,
            "nombre": persona.nombre,
            "apellido": persona.apellido,
            "dni": persona.dni,
            "intereses": getattr(persona, "intereses", ""),
            "display_name": persona.nombre_completo,
            "role": current_user.role,
            "role_label": current_user.role_label,
        },
    }, 200


def actualizar_perfil(payload):
    if not current_user.is_authenticated:
        return {
            "status": "error",
            "message": "Debes iniciar sesión para actualizar el perfil.",
        }, 401

    persona = db.session.get(Persona, current_user.persona_id)
    if persona is None:
        return {
            "status": "error",
            "message": "No se encontró el perfil del usuario.",
        }, 404

    errors = {}
    nombre = payload.get("nombre")
    apellido = payload.get("apellido")
    dni = payload.get("dni")

    if nombre is not None and nombre.strip() != persona.nombre:
        errors["nombre"] = "El campo Nombre no puede modificarse."
    if apellido is not None and apellido.strip() != persona.apellido:
        errors["apellido"] = "El campo Apellido no puede modificarse."
    if dni is not None and dni.strip() != persona.dni:
        errors["dni"] = "El campo DNI no puede modificarse."

    new_email = payload.get("email")
    if new_email is None:
        new_email = persona.email
    new_email = _normalize_email(new_email)

    if not new_email:
        errors["email"] = "El email es obligatorio."

    if errors:
        return {"status": "validation_error", "errors": errors}, 400

    if new_email != persona.email:
        existing = Persona.query.filter_by(email=new_email).first()
        if existing is not None or new_email == persona.email:
            return {
                "status": "validation_error",
                "errors": {"email": "El email ya se encuentra registrado en el sistema."},
            }, 400
        persona.email = new_email

    intereses = payload.get("intereses")
    if intereses is not None:
        persona.intereses = intereses.strip()

    db.session.commit()

    return {
        "status": "ok",
        "profile": {
            "persona_id": persona.persona_id,
            "email": persona.email,
            "nombre": persona.nombre,
            "apellido": persona.apellido,
            "dni": persona.dni,
            "intereses": getattr(persona, "intereses", ""),
            "display_name": persona.nombre_completo,
            "role": current_user.role,
            "role_label": current_user.role_label,
        },
    }, 200
