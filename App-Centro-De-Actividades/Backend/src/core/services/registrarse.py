import json
import re
from pathlib import Path

from sqlalchemy.exc import IntegrityError

from src.core.bcrypt_and_session import bcrypt
from src.core.database import db
from src.core.models.persona import Empleado, Persona, PersonaRolPuente, Rol, Socio
from src.core.services.mailjet_email import (
    EmailDeliveryError,
    generate_temporary_password,
    send_employee_access_email,
)

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PASSWORD_LENGTH_MESSAGE = "La contraseña debe tener entre 6 a 12 caracteres."
REPEAT_PASSWORD_MESSAGE = "Repetir contraseña debe coincidir con la contraseña."
PHONE_INVALID_CHARS_MESSAGE = (
    "Ingrese un telefono valido sin caracteres especiales, letras o espacios. "
    "Ejemplo 2214446633"
)
PHONE_AREA_CODE_MESSAGE = (
    "Debe ingresar un código de área válido en territorio argentino. Ejemplo: 221"
)
PHONE_TOTAL_DIGITS_MESSAGE = (
    'El "Teléfono" debe alcanzar los 10 dígitos totales incluyendo el código de área. '
    "Ejemplo: 2214446633"
)
AREA_CODES_JSON_PATH = (
    Path(__file__).resolve().parents[3] / "assets" / "cod_area_arg.json"
)
VALID_AREA_CODES = frozenset()


def _load_valid_area_codes():
    payload = json.loads(AREA_CODES_JSON_PATH.read_text(encoding="utf-8"))
    return frozenset(
        str(item["codigo_area"]).strip()
        for item in payload.get("codigos_area", [])
        if str(item.get("codigo_area", "")).strip()
    )


VALID_AREA_CODES = _load_valid_area_codes()


def validar_payload_registro(payload):
    return _validar_payload_persona(payload, require_password_fields=True)


def validar_payload_registro_empleado(payload):
    return _validar_payload_persona(payload, require_password_fields=False)


def _validar_payload_persona(payload, require_password_fields):
    normalized_payload = {
        "dni": (payload.get("dni") or "").strip(),
        "email": normalizar_email(payload.get("email") or ""),
        "nombre": (payload.get("nombre") or "").strip(),
        "apellido": (payload.get("apellido") or "").strip(),
        "telefono": (payload.get("telefono") or "").strip(),
        "calle": (payload.get("calle") or "").strip(),
        "numero_puerta": (payload.get("numero_puerta") or "").strip(),
        "codigo_postal": (payload.get("codigo_postal") or "").strip(),
    }
    errors = {}

    if require_password_fields:
        normalized_payload["password"] = payload.get("password") or ""
        normalized_payload["repeat_password"] = payload.get("repeat_password") or ""

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

    if not normalized_payload["telefono"]:
        errors["telefono"] = "El teléfono es obligatorio."
    else:
        telefono_normalizado, telefono_error = validar_telefono_registro(
            normalized_payload["telefono"]
        )
        if telefono_error is not None:
            errors["telefono"] = telefono_error
        else:
            normalized_payload["telefono"] = telefono_normalizado

    if not normalized_payload["calle"]:
        errors["calle"] = "La calle es obligatoria."

    if not normalized_payload["numero_puerta"]:
        errors["numero_puerta"] = "El número de puerta es obligatorio."

    if not normalized_payload["codigo_postal"]:
        errors["codigo_postal"] = "El código postal es obligatorio."

    if require_password_fields:
        if not normalized_payload["password"]:
            errors["password"] = "La contraseña es obligatoria."
        elif not 6 <= len(normalized_payload["password"]) <= 12:
            errors["password"] = PASSWORD_LENGTH_MESSAGE

        if not normalized_payload["repeat_password"]:
            errors["repeat_password"] = "Repetir contraseña es obligatorio."
        elif normalized_payload["repeat_password"] != normalized_payload["password"]:
            errors["repeat_password"] = REPEAT_PASSWORD_MESSAGE

    return normalized_payload, errors


def registrar_socio(payload):
    return _registrar_persona_con_rol(
        payload=payload,
        role_name="socio",
        entity_factory=Socio,
        password=payload["password"],
        missing_role_message=(
            "El registro no está disponible porque falta la configuración del rol socio."
        ),
        success_message="La cuenta ha sido creada con éxito.",
        redirect_to="/login",
    )


def registrar_empleado(payload):
    credenciales = provisionar_acceso_empleado(payload)

    return _registrar_persona_con_rol(
        payload=payload,
        role_name="empleado",
        entity_factory=Empleado,
        password=credenciales["temporary_password"],
        missing_role_message=(
            "El registro no está disponible porque falta la configuración del rol empleado."
        ),
        success_message="El empleado fue registrado correctamente y se envió por email la contraseña temporal.",
        redirect_to="/inicio",
        post_flush_action=lambda persona: _entregar_acceso_empleado(
            payload=payload,
            persona=persona,
            credenciales=credenciales,
        ),
    )


def provisionar_acceso_empleado(payload):
    temporary_password = generate_temporary_password()
    return {
        "temporary_password": temporary_password,
        "delivery_channel": "email",
        "delivery_status": "pending",
        "recipient": payload["email"],
    }


def _entregar_acceso_empleado(*, payload, persona, credenciales):
    send_employee_access_email(
        recipient_email=credenciales["recipient"],
        recipient_name=persona.nombre or payload["nombre"],
        temporary_password=credenciales["temporary_password"],
    )


def _registrar_persona_con_rol(
    *,
    payload,
    role_name,
    entity_factory,
    password,
    missing_role_message,
    success_message,
    redirect_to,
    post_flush_action=None,
):
    if Persona.query.filter_by(dni=payload["dni"]).first() is not None:
        return (
            _validation_error(
                "dni", "El DNI ya se encuentra registrado en el sistema."
            ),
            400,
        )

    if Persona.query.filter_by(email=payload["email"]).first() is not None:
        return (
            _validation_error(
                "email", "El email ya se encuentra registrado en el sistema."
            ),
            400,
        )

    role = Rol.query.filter(db.func.lower(Rol.nombre) == role_name).first()
    if role is None:
        return {"status": "error", "message": missing_role_message}, 503

    persona = Persona(
        dni=payload["dni"],
        email=payload["email"],
        password_hash=bcrypt.generate_password_hash(password).decode("utf-8"),
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
        db.session.add(entity_factory(persona_id=persona.persona_id))
        db.session.add(
            PersonaRolPuente(persona_id=persona.persona_id, rol_id=role.rol_id)
        )
        if post_flush_action is not None:
            post_flush_action(persona)
        db.session.commit()
    except IntegrityError as error:
        db.session.rollback()
        return _integrity_error_response(error)
    except EmailDeliveryError as error:
        db.session.rollback()
        return {"status": "error", "message": str(error)}, 503

    return {
        "status": "registered",
        "message": success_message,
        "redirect_to": redirect_to,
    }, 201


def normalizar_email(email):
    return email.strip().lower()


def validar_telefono_registro(telefono):
    if not telefono.isdigit():
        return None, PHONE_INVALID_CHARS_MESSAGE

    if len(telefono) != 10:
        return None, PHONE_TOTAL_DIGITS_MESSAGE

    telefono_normalizado = telefono.strip()

    if not _codigo_area_valido(telefono_normalizado):
        return None, PHONE_AREA_CODE_MESSAGE

    return telefono_normalizado, None


def _codigo_area_valido(telefono):
    for area_length in range(4, 1, -1):
        candidate_code = telefono[:area_length]
        if candidate_code in VALID_AREA_CODES:
            subscriber_length = len(telefono[area_length:])
            return 6 <= subscriber_length <= 8

    return False


def _validation_error(field, message):
    return {"status": "validation_error", "errors": {field: message}}


def _integrity_error_response(error):
    detail = str(getattr(error, "orig", error)).lower()

    if "dni" in detail:
        return (
            _validation_error(
                "dni", "El DNI ya se encuentra registrado en el sistema."
            ),
            400,
        )

    if "email" in detail:
        return (
            _validation_error(
                "email", "El email ya se encuentra registrado en el sistema."
            ),
            400,
        )

    return {
        "status": "error",
        "message": "No se pudo completar el registro por un conflicto de datos.",
    }, 409
