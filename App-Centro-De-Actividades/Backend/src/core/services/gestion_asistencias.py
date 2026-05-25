from zoneinfo import ZoneInfo
# import jwt
# import os
from datetime import datetime, timedelta
from flask_login import current_user
from src.core.database import db
from src.core.models.reserva import Reserva
from src.core.models.clase import Clase
from src.core.models.persona import Persona, Socio
from src.core.models.qr_asistencia import QrAsistencia
import secrets
from src.core.models.asistencia import Asistencia
from src.core.models.qr_asistencia import QrAsistencia

class BusinessException(Exception):
    """Excepción base para reglas de negocio infringidas."""
    pass

class ReservaNoEncontradaException(BusinessException):
    pass

class FueraDeHorarioException(BusinessException):
    pass

class ClienteNoAsociadoException(BusinessException):
    pass

class AutenticacionRequeridaException(BusinessException):
    pass

class AccesoQRDenegadoException(BusinessException):
    pass

class QRInvalidoException(BusinessException):
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

    _validar_acceso_generacion_qr(reserva)

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

    # if ahora < limite_inferior:
    #     raise FueraDeHorarioException("Aún es temprano. Podrás visualizar tu QR 15 minutos antes de la clase.")

    # if ahora > limite_superior:
    #     raise FueraDeHorarioException("El margen de tiempo de 15 minutos para ingresar ha expirado.")

    if not (limite_inferior <= ahora <= limite_superior):
        raise FueraDeHorarioException(
            "El QR solo puede visualizarse dentro de los 15 minutos antes y después del inicio de la clase."
        )
    
    # Generar y persistir un token de QR para esta reserva
    token = secrets.token_urlsafe(32)
    expira_en = limite_superior

    qr = QrAsistencia(
        reserva_id=reserva.reserva_id,
        token_hash=token,
        expira_en=expira_en,
    )
    db.session.add(qr)
    db.session.commit()

    return {
        "dni": persona.dni,
        "id_reserva": id_reserva_real,
        "nombre": persona.nombre,
        "clase": clase.actividad.name.capitalize() if hasattr(clase.actividad, 'name') else str(clase.actividad),
        "ya_asistio": False,
        "token": token,
    }

def registrar_asistencia(dni, id_reserva, id_clase):
    """Ejecuta los controles de validación de ingreso y registra el presente en la BD."""
    # 1. Buscamos la reserva real
    reserva = db.session.get(Reserva, id_reserva)
    if not reserva:
        raise ReservaNoEncontradaException("El QR es inválido.")

    # 2. Buscamos la persona por el DNI provisto en el QR para validar consistencia
    persona = Persona.query.filter_by(dni=str(dni).strip()).first()

    if not persona or reserva.socio_id != persona.persona_id:
        raise QRInvalidoException("El QR es inválido.")

    _validar_acceso_escaneo_qr(reserva, persona)

    if id_clase is not None:
        if int(reserva.clase_id) != int(id_clase):
            raise AccesoQRDenegadoException(
                "El QR escaneado no corresponde a la clase seleccionada."
            )

    # 3. Validación: Impedir duplicados controlando el estado string de tu modelo
    if reserva.estado == "asistio":
        raise AsistenciaYaRegistradaException(
            f"El código QR de {persona.nombre_completo} para la clase de "
            f"{reserva.clase.actividad.value} ya fue escaneado."
        )

    # 4. Acción positiva: Cambiamos el estado a 'asistio' y guardamos en Postgres
    reserva.estado = "asistio"

    # Si existe un QR asociado a la reserva, marcamos su escaneo
    qr = None
    try:
        qr = QrAsistencia.query.filter_by(reserva_id=reserva.reserva_id).order_by(QrAsistencia.generado_en.desc()).first()
    except Exception:
        qr = None

    asistencia = Asistencia(
        reserva_id=reserva.reserva_id,
        qr_asistencia_id=qr.qr_asistencia_id if qr is not None else None,
        medio_registro="qr",
    )

    if qr is not None:
        qr.escaneado_en = db.func.now()
        qr.estado = "escaneado"
        db.session.add(qr)

    db.session.add(asistencia)
    db.session.commit()

    return f"Asistencia registrada con éxito para {persona.nombre_completo} en la clase de {reserva.clase.actividad.value}."


def registrar_asistencia_manual(reserva_id):
    """Registra la asistencia de forma manual (para empleados desde el panel)."""
    # 1. Validar que el usuario es empleado
    if not current_user.is_authenticated:
        raise AutenticacionRequeridaException("Debes iniciar sesión para registrar asistencia.")
    
    if getattr(current_user, "role", None) != "empleado":
        raise AccesoQRDenegadoException("Solo los empleados pueden registrar asistencia manualmente.")
    
    # 2. Obtener la reserva
    reserva = db.session.get(Reserva, reserva_id)
    if not reserva:
        raise ReservaNoEncontradaException(f"No se encontró la reserva con ID {reserva_id}.")
    
    # 3. Validar que la reserva esté confirmada o con pago pendiente
    if reserva.estado not in ["confirmada", "pendiente_pago"]:
        if reserva.estado == "asistio":
            raise AsistenciaYaRegistradaException(
                f"La asistencia para esta reserva ya fue registrada."
            )
        raise AccesoQRDenegadoException(
            f"No se puede registrar asistencia para una reserva en estado '{reserva.estado}'."
        )

    clase = db.session.get(Clase, reserva.clase_id)
    if not clase:
        raise ReservaNoEncontradaException("No se encontró la clase asociada a la reserva.")

    inicio_clase_dt = datetime.combine(clase.fecha, clase.horario_inicio)
    tz_argentina = ZoneInfo("America/Argentina/Buenos_Aires")
    ahora = datetime.now(tz_argentina).replace(tzinfo=None)

    limite_inferior = inicio_clase_dt - timedelta(minutes=15)
    limite_superior = inicio_clase_dt + timedelta(minutes=15)

    if not (limite_inferior <= ahora <= limite_superior):
        raise FueraDeHorarioException(
            "La asistencia solo puede registrarse dentro de los 15 minutos antes y después del inicio de la clase."
        )
    
    # 4. Registrar la asistencia
    reserva.estado = "asistio"

    asistencia = Asistencia(
        reserva_id=reserva.reserva_id,
        empleado_registro_id=getattr(current_user, "persona_id", None),
        medio_registro="manual",
    )

    db.session.add(asistencia)
    db.session.commit()

    persona = Persona.query.get(reserva.socio_id)
    return f"Asistencia registrada con éxito para {persona.nombre_completo}."


def _validar_acceso_generacion_qr(reserva):
    if not current_user.is_authenticated:
        raise AutenticacionRequeridaException(
            "Debes iniciar sesión para generar el QR de asistencia."
        )

    if getattr(current_user, "role", None) != "socio":
        raise AccesoQRDenegadoException(
            "Solo los socios pueden generar códigos QR de asistencia."
        )

    if reserva.socio_id != current_user.persona_id:
        raise AccesoQRDenegadoException(
            "Solo puedes generar el QR de tus propias reservas."
        )


def _validar_acceso_escaneo_qr(reserva, persona):
    if not current_user.is_authenticated:
        raise AutenticacionRequeridaException(
            "Debes iniciar sesión para generar códigos QR de asistencia."
        )

    if getattr(current_user, "role", None) == "socio":
        if reserva.socio_id != current_user.persona_id or persona.persona_id != current_user.persona_id:
            raise AccesoQRDenegadoException(
                "Como socio solo puedes generar  tus propios códigos QR de asistencia."
            )

