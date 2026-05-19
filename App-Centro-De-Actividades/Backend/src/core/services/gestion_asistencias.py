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
    """
    Valida la reserva y retorna el payload para el QR.
    Soporta que la reserva venga de la BD o estructurada como dict.
    """
    # Force la consulta limpia al ORM usando el ID numérico
    reserva = db.session.query(Reserva).filter(Reserva.reserva_id == reserva_id).first()
    
    if not reserva:
        raise ReservaNoEncontradaException(f"No se encontró la reserva con ID {reserva_id}.")

    # Control de contingencia: Si por algún motivo previo se transformó en un dict
    if isinstance(reserva, dict):
        id_socio = reserva.get("socio_id")
        id_reserva_real = reserva.get("reserva_id")
        reserva_objeto = db.session.query(Reserva).filter(Reserva.reserva_id == id_reserva_real).first()
        clase = reserva_objeto.clase
        estado_reserva = reserva.get("estado")
    else:
        # Comportamiento normal con el Modelo ORM
        id_socio = reserva.get("socio_id") if isinstance(reserva, dict) else reserva.socio_id
        clase = reserva.clase
        id_reserva_real = reserva.reserva_id
        estado_reserva = reserva.estado

    # Buscar la persona/socio para extraer los datos del QR
    persona = db.session.query(Persona).filter(Persona.persona_id == id_socio).first()
    if not persona:
        raise ReservaNoEncontradaException("No se encontró el socio vinculado a la reserva.")

    # --- Validación de Horarios (+/- 15 minutos) ---
    inicio_clase_dt = datetime.combine(clase.fecha, clase.horario_inicio)
    ahora = datetime.now()

    limite_inferior = inicio_clase_dt - timedelta(minutes=15)
    limite_superior = inicio_clase_dt + timedelta(minutes=15)

    if estado_reserva == "asistio":
        raise FueraDeHorarioException("Ya registraste tu asistencia para esta clase.")

    if ahora < limite_inferior:
        raise FueraDeHorarioException("Aún es temprano. Podrás visualizar tu QR 15 minutos antes de la clase.")

    if ahora > limite_superior:
        raise FueraDeHorarioException("El margen de tiempo de 15 minutos para ingresar ha expirado.")

    # Retorno exitoso del payload plano
    return {
        "dni": persona.dni,
        "id_reserva": id_reserva_real,
        "nombre": persona.nombre,
        "apellido": persona.apellido,
        "clase": clase.actividad.name.capitalize() if hasattr(clase.actividad, 'name') else str(clase.actividad)
    }

def registrar_asistencia(dni, id_reserva):
    """Ejecuta los controles de validación de ingreso y registra el presente en la BD."""
    # 1. Buscamos la reserva real
    reserva = Reserva.query.get(id_reserva)
    if not reserva:
        raise ReservaNoEncontradaException("El QR es inválido.")

    # 2. Buscamos la persona por el DNI provisto en el QR para validar consistencia
    persona = Persona.query.filter_by(dni=str(dni)).first()
    
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