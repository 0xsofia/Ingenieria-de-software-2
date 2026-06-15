from src.core.database import db
from src.core.models.persona import Persona
from src.core.services.mailjet_email import send_password_recovery_email, EmailDeliveryError
import secrets

def solicitar_recuperacion(email: str):
    persona = Persona.query.filter_by(email=email).first()
    
    if not persona:
        return {"status": "error", "message": "El email ingresado no se encuentra registrado."}, 404
        
    # Generate a secure random token
    token = secrets.token_urlsafe(32)
    
    # Save the token in the database
    persona.token_recuperacion = token
    db.session.commit()
    
    try:
        send_password_recovery_email(
            recipient_email=persona.email,
            recipient_name=persona.nombre,
            token=token
        )
    except EmailDeliveryError as e:
        # Rollback token if email fails
        persona.token_recuperacion = None
        db.session.commit()
        return {"status": "error", "message": str(e)}, 500
    
    # For this HU, we return the token in the response so the frontend can use it for testing
    return {
        "status": "success", 
        "message": "Se ha enviado un email con las instrucciones para recuperar su contraseña",
        "token": token
    }, 200
