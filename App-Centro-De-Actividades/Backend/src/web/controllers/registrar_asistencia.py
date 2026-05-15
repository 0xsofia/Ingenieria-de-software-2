from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from src.core.database import db
from src.core.models.asistencia import QrAsistencia, Asistencia, Reserva
from src.core.models.persona import Empleado

registrar_asistencia_bp = Blueprint("registrar_asistencia", __name__, url_prefix="/api/asistencia")


@registrar_asistencia_bp.route("/registrar", methods=["POST"])
@login_required
def registrar_asistencia():
    """Registra asistencia escaneando un token QR."""
    data = request.get_json()
    token = data.get("token")

    if not token:
        return jsonify({"error": "Token QR requerido"}), 400

    # Verificar que el usuario actual sea empleado
    empleado = Empleado.query.filter_by(persona_id=current_user.persona_id).first()
    if not empleado:
        return jsonify({"error": "Solo empleados pueden registrar asistencia"}), 403

    # Buscar el QR por token
    qr = QrAsistencia.query.filter_by(token_hash=token.strip()).first()
    if not qr:
        return jsonify({"error": "Token QR inválido"}), 404

    # Verificar estado del QR
    if qr.estado != "activo":
        return jsonify({"error": "Token QR ya utilizado o expirado"}), 400

    # Verificar expiración
    if qr.expira_en < datetime.utcnow():
        return jsonify({"error": "Token QR expirado"}), 400

    # Verificar que no haya asistencia ya registrada para esta reserva
    asistencia_existente = Asistencia.query.filter_by(reserva_id=qr.reserva_id).first()
    if asistencia_existente:
        return jsonify({"error": "Asistencia ya registrada para esta reserva"}), 400

    # Obtener la reserva
    reserva = Reserva.query.get(qr.reserva_id)
    if not reserva or reserva.estado != "confirmada":
        return jsonify({"error": "Reserva no válida para asistencia"}), 400

    # Marcar QR como usado
    qr.escaneado_en = datetime.utcnow()
    qr.estado = "usado"

    # Crear asistencia
    asistencia = Asistencia(
        reserva_id=qr.reserva_id,
        qr_asistencia_id=qr.qr_asistencia_id,
        empleado_registro_id=empleado.persona_id,
        fecha_hora=datetime.utcnow(),
        medio_registro="qr",
    )

    # Actualizar estado de la reserva
    reserva.estado = "asistida"

    db.session.add(asistencia)
    db.session.commit()

    return jsonify({
        "message": "Asistencia registrada exitosamente",
        "asistencia_id": asistencia.asistencia_id,
        "reserva_id": reserva.reserva_id,
        "socio": reserva.socio.persona.nombre_completo,
        "clase": f"{reserva.clase.actividad.nombre} - {reserva.clase.fecha_clase}",
    }), 201


@registrar_asistencia_bp.route("/qr/<token>", methods=["GET"])
@login_required
def validar_qr(token):
    """Valida un token QR sin registrar asistencia (para preview)."""
    empleado = Empleado.query.filter_by(persona_id=current_user.persona_id).first()
    if not empleado:
        return jsonify({"error": "Solo empleados pueden validar QR"}), 403

    qr = QrAsistencia.query.filter_by(token_hash=token.strip()).first()
    if not qr:
        return jsonify({"error": "Token QR inválido"}), 404

    reserva = Reserva.query.get(qr.reserva_id)
    if not reserva:
        return jsonify({"error": "Reserva no encontrada"}), 404

    asistencia_existente = Asistencia.query.filter_by(reserva_id=qr.reserva_id).first()

    return jsonify({
        "valido": qr.estado == "activo" and qr.expira_en > datetime.utcnow() and not asistencia_existente,
        "estado_qr": qr.estado,
        "expirado": qr.expira_en < datetime.utcnow(),
        "asistencia_existente": asistencia_existente is not None,
        "socio": reserva.socio.persona.nombre_completo,
        "clase": f"{reserva.clase.actividad.nombre} - {reserva.clase.fecha_clase}",
        "fecha_clase": reserva.clase.fecha_clase.isoformat(),
        "hora_inicio": reserva.clase.hora_inicio.strftime("%H:%M"),
    }), 200
