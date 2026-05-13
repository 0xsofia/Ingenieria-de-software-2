import re

from sqlalchemy.exc import IntegrityError

from src.core.bcrypt_and_session import bcrypt
from src.core.database import db
from src.core.models.persona import Persona, PersonaRolPuente, Rol, Socio

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def validar_payload_registro(payload):
    normalized_payload = {
        "dni": (payload.get("dni") or "").strip(),
        "email": normalizar_email(payload.get("email") or ""),
        "nombre": (payload.get("nombre") or "").strip(),
        "apellido": (payload.get("apellido") or "").strip(),
        "telefono": (payload.get("telefono") or "").strip(),
        "calle": (payload.get("calle") or "").strip(),
        "numero_puerta": (payload.get("numero_puerta") or "").strip(),
        "codigo_postal": (payload.get("codigo_postal") or "").strip(),
        "password": payload.get("password") or "",
        "repeat_password": payload.get("repeat_password") or "",
    }
    errors = {}

    if not normalized_payload["dni"]:
        errors["dni"] = "El DNI es obligatorio."
    elif not normalized_payload["dni"].isdigit():
        errors["dni"] = "Ingresá el DNI solo con números."

    if not normalized_payload["email"]:
        errors["email"] = "El email es obligatorio."
    elif not EMAIL_PATTERN.match(normalized_payload["email"]):
        errors["email"] = "Ingresá un email válido."

    if not normalized_payload["nombre"]:
        errors["nombre"] = "El nombre es obligatorio."

    if not normalized_payload["apellido"]:
        errors["apellido"] = "El apellido es obligatorio."

    telefono_normalizado = normalizar_telefono(normalized_payload["telefono"])
    if not normalized_payload["telefono"]:
        errors["telefono"] = "El teléfono es obligatorio."
    elif telefono_normalizado is None:
        errors["telefono"] = (
            "Ingresá un celular válido sin 0 ni 15. Ejemplo: 22112345678."
        )
    else:
        normalized_payload["telefono"] = telefono_normalizado

    if not normalized_payload["calle"]:
        errors["calle"] = "La calle es obligatoria."

    if not normalized_payload["numero_puerta"]:
        errors["numero_puerta"] = "El número de puerta es obligatorio."

    if not normalized_payload["codigo_postal"]:
        errors["codigo_postal"] = "El código postal es obligatorio."

    if not normalized_payload["password"]:
        errors["password"] = "La contraseña es obligatoria."
    elif len(normalized_payload["password"]) < 4:
        errors["password"] = "La contraseña debe tener al menos 4 caracteres."
    elif len(normalized_payload["password"]) > 128:
        errors["password"] = "La contraseña debe tener como máximo 128 caracteres."

    if not normalized_payload["repeat_password"]:
        errors["repeat_password"] = "Repetir contraseña es obligatorio."
    elif normalized_payload["repeat_password"] != normalized_payload["password"]:
        errors["repeat_password"] = (
            "Repetir contraseña debe coincidir con la contraseña."
        )

    return normalized_payload, errors


def registrar_socio(payload):
    if Persona.query.filter_by(dni=payload["dni"]).first() is not None:
        return _validation_error("dni", "El DNI ya se encuentra registrado en el sistema."), 400

    if Persona.query.filter_by(email=payload["email"]).first() is not None:
        return _validation_error("email", "El email ya se encuentra registrado en el sistema."), 400

    role = Rol.query.filter(db.func.lower(Rol.nombre) == "socio").first()
    if role is None:
        return {
            "status": "error",
            "message": "El registro no está disponible porque falta la configuración del rol socio.",
        }, 503

    persona = Persona(
        dni=payload["dni"],
        email=payload["email"],
        password_hash=bcrypt.generate_password_hash(payload["password"]).decode("utf-8"),
        nombre=payload["nombre"],
        apellido=payload["apellido"],
        telefono=payload["telefono"],
        calle=payload["calle"],
        numero_puerta=payload["numero_puerta"],
        codigo_postal=payload["codigo_postal"],
        estado="activo",
    )

    try:
        db.session.add(persona)
        db.session.flush()
        db.session.add(Socio(persona_id=persona.persona_id))
        db.session.add(PersonaRolPuente(persona_id=persona.persona_id, rol_id=role.rol_id))
        db.session.commit()
    except IntegrityError as error:
        db.session.rollback()
        return _integrity_error_response(error)

    return {
        "status": "registered",
        "message": "La cuenta ha sido creada con éxito.",
        "redirect_to": "/login",
    }, 201


def normalizar_email(email):
    return email.strip().lower()


def normalizar_telefono(telefono):
    digits = re.sub(r"\D", "", telefono or "")

    if digits.startswith("54"):
        digits = digits[2:]

    if digits.startswith("0"):
        digits = digits[1:]

    local_phone = _normalizar_digitos_locales(digits)
    if local_phone is None:
        return None

    return f"+54{local_phone}"


def _normalizar_digitos_locales(digits):
    for area_length in range(2, 5):
        local_phone = _validar_telefono_local(digits, area_length)
        if local_phone is not None:
            return local_phone

        local_phone = _validar_telefono_con_prefijo_legacy(digits, area_length)
        if local_phone is not None:
            return local_phone

    return None


def _validar_telefono_local(digits, area_length):
    subscriber = digits[area_length:]
    if len(subscriber) < 6 or len(subscriber) > 8:
        return None

    if 10 <= area_length + len(subscriber) <= 11:
        return digits

    return None


def _validar_telefono_con_prefijo_legacy(digits, area_length):
    if digits[area_length : area_length + 2] != "15":
        return None

    subscriber = digits[area_length + 2 :]
    if len(subscriber) < 6 or len(subscriber) > 8:
        return None

    local_phone = f"{digits[:area_length]}{subscriber}"
    if 10 <= len(local_phone) <= 11:
        return local_phone

    return None


def _validation_error(field, message):
    return {"status": "validation_error", "errors": {field: message}}


def _integrity_error_response(error):
    detail = str(getattr(error, "orig", error)).lower()

    if "dni" in detail:
        return _validation_error("dni", "El DNI ya se encuentra registrado en el sistema."), 400

    if "email" in detail:
        return _validation_error("email", "El email ya se encuentra registrado en el sistema."), 400

    return {
        "status": "error",
        "message": "No se pudo completar el registro por un conflicto de datos.",
    }, 409
