from zoneinfo import ZoneInfo
import jwt
import os
from datetime import datetime, timedelta
from src.core.database import db
from src.core.models.reserva import Reserva
from src.core.models.clase import Clase
from src.core.models.persona import Persona, Socio

class BusinessException(Exception):
    """Excepción base para reglas de negocio infringidas."""
    pass

class ReservaNoEncontradaException(BusinessException):
    pass

class FueraDeHorarioException(BusinessException):
    pass

class ClienteNoAsociadoException(BusinessException):
    pass

class AsistenciaYaRegistradaException(BusinessException):
    pass

class HorarioInvalidoException(Exception): pass


def generar_token_asistencia(reserva_id):
    # 🚀 FORZAMOS UN JOIN LIMPIO: Traemos la Reserva y su Clase correspondiente en una sola consulta
    resultado = db.session.query(Reserva, Clase)\
        .join(Clase, Reserva.clase_id == Clase.clase_id)\
        .filter(Reserva.reserva_id == reserva_id)\
        .first()
    
    if not resultado:
        raise ReservaNoEncontradaException(f"No se encontró la reserva con ID {reserva_id} o su clase asociada.")

    # Al hacer una query de dos modelos, SQLAlchemy nos devuelve una tupla desestructurable:
    reserva, clase = resultado

    id_socio = reserva.socio_id
    id_reserva_real = reserva.reserva_id
    estado_reserva = reserva.estado

    # Buscamos el socio asociado
    persona = db.session.query(Persona).filter(Persona.persona_id == id_socio).first()
    if not persona:
        raise ReservaNoEncontradaException("No se encontró el socio vinculado a la reserva.")

    if estado_reserva == "asistio":
        return {
            "dni": persona.dni,
            "id_reserva": id_reserva_real,
            "nombre": persona.nombre,
            "clase": clase.actividad.name.capitalize() if hasattr(clase.actividad, 'name') else str(clase.actividad),
            "ya_asistio": True
        }

    # ⏰ Ahora 'clase' viene 100% verificado desde el JOIN explícito de la query
    inicio_clase_dt = datetime.combine(clase.fecha, clase.horario_inicio)

    tz_argentina = ZoneInfo("America/Argentina/Buenos_Aires")
    ahora = datetime.now(tz_argentina).replace(tzinfo=None) 

    limite_inferior = inicio_clase_dt - timedelta(minutes=15)
    limite_superior = inicio_clase_dt + timedelta(minutes=15)
    
    # print(f"\n🔍 DEBUG RESERVA ID: {reserva_id}", flush=True)
    # print(f"⏰ HORA ACTUAL DEL SISTEMA: {ahora.strftime('%H:%M:%S')}", flush=True)
    # print(f"📌 MARGEN INFERIOR PERMITIDO: {limite_inferior.strftime('%H:%M:%S')}", flush=True)
    # print(f"📌 MARGEN SUPERIOR PERMITIDO: {limite_superior.strftime('%H:%M:%S')}\n", flush=True)

    if ahora < limite_inferior:
        raise FueraDeHorarioException("Aún es temprano. Podrás visualizar tu QR 15 minutos antes de la clase.")

    if ahora > limite_superior:
        raise FueraDeHorarioException("El margen de tiempo de 15 minutos para ingresar ha expirado.")
    
    return {
        "dni": persona.dni,
        "id_reserva": id_reserva_real,
        "nombre": persona.nombre,
        "clase": clase.actividad.name.capitalize() if hasattr(clase.actividad, 'name') else str(clase.actividad),
        "ya_asistio": False
    }

def registrar_asistencia(dni, id_reserva, id_clase):
    """Ejecuta los controles de validación de ingreso y registra el presente en la BD."""
    # 1. Buscamos la reserva real
    reserva = Reserva.query.get(id_reserva)
    if not reserva:
        raise ReservaNoEncontradaException("El QR es inválido.")

    # 2. Buscamos la persona por el DNI provisto en el QR para validar consistencia
    persona = Persona.query.filter_by(dni=str(dni)).first()
    # clase = Clase.query.get(id_clase).first() 

    if id_clase is not None:
        clase_reserva_id = reserva.clase_id if hasattr(reserva, 'clase_id') else reserva.clase.clase_id
        
        if int(clase_reserva_id) != int(id_clase):
            raise ClienteNoAsociadoException(
                "La reserva escaneada corresponde a otra clase o turno horario diferente."
            )
    
    # Validación: Que el DNI pertenezca al dueño de la reserva
    if not persona or reserva.socio_id != persona.persona_id:
        raise ClienteNoAsociadoException("El cliente no está registrado para la clase seleccionada.")

    # 3. Validación: Impedir duplicados controlando el estado string de tu modelo
    if reserva.estado == "asistio":
        raise AsistenciaYaRegistradaException(
            f"El código QR de {persona.nombre_completo} para la clase de "
            f"{reserva.clase.actividad.value} ya fue escaneado."
        )

    # 4. Acción positiva: Cambiamos el estado a 'asistio' y guardamos en Postgres
    reserva.estado = "asistio"
    db.session.commit()
    
    return f"Asistencia registrada con éxito para {persona.nombre_completo} en la clase de {reserva.clase.actividad.value}."


# def registrar_asistencia_qr(token):
#     """Desencripta un token JWT e impacta la asistencia de forma directa."""
#     try:
#         payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
        
#         # Usamos el método de clase que ya contiene todas las validaciones de negocio e impacta la BD
#         return registrar_asistencia(
#             dni=payload.get('dni'), 
#             id_reserva=payload.get('id_reserva')
#         )
        
#     except jwt.ExpiredSignatureError:
#         raise ValueError("El QR ha expirado")
#     except jwt.InvalidTokenError:
#         raise ValueError("QR inválido")