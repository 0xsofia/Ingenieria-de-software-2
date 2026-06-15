from src.core.database import db
from src.core.models.persona import Persona
from src.core.bcrypt_and_session import bcrypt


def cambiar_contrasena(
    email: str, current_password: str, new_password: str, token: str = None
):
    if token:
        persona = Persona.query.filter_by(token_recuperacion=token).first()
        if not persona:
            return {
                "status": "error",
                "message": "Este email de recuperacion ya ha sido utilizado, recupere su contraseña nuevamente",
            }, 400

        # Clear the token so it can't be used again
        persona.token_recuperacion = None
    else:
        persona = Persona.query.filter_by(email=email).first()
        if not persona:
            return {"status": "error", "message": "Usuario no encontrado."}, 404

        if not bcrypt.check_password_hash(persona.password_hash, current_password):
            return {
                "status": "error",
                "message": "La contraseña actual ingresada no coincide con la registrada en el sistema",
            }, 400

    persona.password_hash = bcrypt.generate_password_hash(new_password).decode("utf-8")
    db.session.commit()

    return {
        "status": "success",
        "message": "Su contraseña ha sido cambiada exitosamente",
    }, 200
