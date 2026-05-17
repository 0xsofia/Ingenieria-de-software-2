from flask import Flask,Blueprint, request, jsonify
from ...core.database import db
from ...core.services.gestion_asistencias import AsistenciaService

session_bp = Blueprint('scanQR', __name__, url_prefix='/api/scanQR')

@session_bp.route('/api/asistencia/generar/<int:reserva_id>', methods=['GET'])
def endpoint_generar_qr(reserva_id):
    try:
        token = AsistenciaService.generar_token_asistencia(reserva_id)
        return jsonify({"token": token}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 403