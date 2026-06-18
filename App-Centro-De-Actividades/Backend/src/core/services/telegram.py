import os
import secrets
from datetime import datetime, timezone, timedelta
import requests

from src.core.database import db
from src.core.models.confirmacion_turno import ConfirmacionTurno
from src.core.models.persona import Persona



def generar_token_confirmacion():
    """Genera un token aleatorio de 32 caracteres."""
    return secrets.token_urlsafe(24)[:32]


def crear_confirmacion_turno(lista_espera_id, socio_id, duracion_minutos=15):
    """
    Crea un token de confirmación en la BD.
    
    Args:
        lista_espera_id: ID del registro en lista_espera
        socio_id: ID del socio
        duracion_minutos: minutos antes de expirar (default 15)
    
    Returns:
        token generado o None si falla
    """
    ahora = _now()
    expira_en = ahora + timedelta(minutes=duracion_minutos)
    token = generar_token_confirmacion()
    
    try:
        confirmacion = ConfirmacionTurno(
            lista_espera_id=lista_espera_id,
            socio_id=socio_id,
            token=token,
            estado="pendiente",
            expira_en=expira_en,
        )
        db.session.add(confirmacion)
        db.session.flush()
        return token
    except Exception as e:
        print(f"Error creando confirmacion_turno: {e}")
        return None


def enviar_mensaje_telegram(socio_id, lista_espera_id, clase_data, token):
    """
    Envía un mensaje de Telegram con la oferta de cupo.
    
    Args:
        socio_id: ID del socio
        lista_espera_id: ID del registro en lista_espera
        clase_data: dict con {actividad, fecha, horario_inicio, horario_fin, cancha}
        token: token de confirmación
    
    Returns:
        True si se envió exitosamente, False en caso contrario
    """
    telegram_bot_token = (os.environ.get('TELEGRAM_BOT_TOKEN') or '').strip()
    telegram_chat_id = (os.environ.get('TELEGRAM_CHAT_ID') or '').strip()
    frontend_base_url = (os.environ.get('FRONTEND_BASE_URL') or 'http://localhost:5173').strip()
    
    if not telegram_bot_token:
        print("WARNING: TELEGRAM_BOT_TOKEN no configurado, saltando envío")
        return False
    
    if not telegram_chat_id:
        print(f"WARNING: TELEGRAM_CHAT_ID no configurado, saltando envío para socio {socio_id}")
        return False
    
    try:
        actividad = clase_data.get('actividad', 'Actividad')
        fecha = clase_data.get('fecha', '')
        horario_inicio = clase_data.get('horario_inicio', '--:--')
        horario_fin = clase_data.get('horario_fin', '--:--')
        cancha = clase_data.get('cancha', '')
        
        confirmacion_url = f"{frontend_base_url}confirmar-turno/{token}"
        
       
        persona = Persona.query.get(socio_id)
        socio_nombre = persona.nombre_completo if persona else 'socio'
        
        mensaje = (
            f"¡Hola {socio_nombre}!\n\n"
            f"🎉 ¡Cupo disponible!\n\n"
            f"<b>{actividad}</b>\n"
            f"📅 Fecha: {fecha}\n"
            f"🕒 Horario: {horario_inicio} - {horario_fin}\n"
            f"🏟️ Cancha: {cancha}\n\n"
            f"⏱️ Tienes 15 minutos para confirmar.\n\n"
        )
        
        url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
        payload = {
            "chat_id": telegram_chat_id,
            "text": mensaje,
            "reply_markup": {
                "inline_keyboard": [
                    [
                        {
                            "text": "✅ Confirmar Turno",
                            "url": confirmacion_url
                        }
                    ]
                ]
            },
            "parse_mode": "HTML",
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print(f"Mensaje Telegram enviado para socio {socio_id}")
            return True
        else:
            print(f"Error enviando Telegram: {response.status_code} - {response.text}")
            return False
    
    except Exception as e:
        print(f"Error enviando mensaje Telegram: {e}")
        return False


def validar_token(token):
    """
    Valida que el token sea válido y no esté expirado.
    
    Args:
        token: token a validar
    
    Returns:
        tuple (confirmacion_obj, error_dict) - si error_dict es None, token es válido
    """
    confirmacion = ConfirmacionTurno.query.filter_by(token=token).first()
    
    if confirmacion is None:
        return None, {"status": "error", "message": "Token inválido o expirado."}
    
    if confirmacion.estado != "pendiente":
        return None, {
            "status": "error",
            "message": f"El token ya fue {confirmacion.estado}.",
        }
    
    ahora = _now()
    if confirmacion.expira_en <= ahora:
        confirmacion.estado = "expirado"
        db.session.flush()
        return None, {"status": "error", "message": "El tiempo de 15 minutos para confirmar el turno ha expirado, no puede acceder al cupo"}
    
    return confirmacion, None


def marcar_confirmacion_como_confirmada(token):
    """
    Marca un token como confirmado.
    
    Args:
        token: token a marcar
    
    Returns:
        confirmacion_turno object o None
    """
    confirmacion = ConfirmacionTurno.query.filter_by(token=token).first()
    
    if confirmacion:
        confirmacion.estado = "confirmado"
        confirmacion.confirmado_en = _now()
        db.session.flush()
        return confirmacion
    
    return None


def _now():
    return datetime.now(tz=timezone.utc)


def notificar_cancelacion_clase(socio_id, lista_espera_id, clase_data, token):
    """
    Envía un mensaje de Telegram notificando la cancelacion de la clase.
    
    Args:
        socio_id: ID del socio
        clase_data: dict con {actividad, fecha, horario_inicio, horario_fin, cancha}

    
    Returns:
        True si se envió exitosamente, False en caso contrario
    """
    telegram_bot_token = (os.environ.get('TELEGRAM_BOT_TOKEN') or '').strip()
    telegram_chat_id = (os.environ.get('TELEGRAM_CHAT_ID') or '').strip()
    frontend_base_url = (os.environ.get('FRONTEND_BASE_URL') or 'http://localhost:5173').strip()
    
    if not telegram_bot_token:
        print("WARNING: TELEGRAM_BOT_TOKEN no configurado, saltando envío")
        return False
    
    if not telegram_chat_id:
        print(f"WARNING: TELEGRAM_CHAT_ID no configurado, saltando envío para socio {socio_id}")
        return False
    
    try:
        actividad = clase_data.get('actividad', 'Actividad')
        fecha = clase_data.get('fecha', '')
        horario_inicio = clase_data.get('horario_inicio', '--:--')
        horario_fin = clase_data.get('horario_fin', '--:--')
        cancha = clase_data.get('cancha', '')
        
        persona = Persona.query.get(socio_id)
        socio_nombre = persona.nombre_completo if persona else 'socio'
        
        mensaje = (
            f"¡Hola {socio_nombre}!\n\n"
            f"La clase de <b>{actividad}</b>\n"
            f"📅 Fecha: {fecha}\n"
            f"🕒 Horario: {horario_inicio} - {horario_fin}\n"
            f"🏟️ Cancha: {cancha}\n\n"
            f"Ha sido cancelada.\n\n"
            f"Hemos registrado un crédito a favor en su cuenta para que lo utilice en su próxima reserva.\n"
        )
        
        url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
        payload = {
            "chat_id": telegram_chat_id,
            "text": mensaje,
            "parse_mode": "HTML",
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print(f"Mensaje Telegram enviado para socio {socio_id}")
            return True
        else:
            print(f"Error enviando Telegram: {response.status_code} - {response.text}")
            return False
    
    except Exception as e:
        print(f"Error enviando mensaje Telegram: {e}")
        return False
