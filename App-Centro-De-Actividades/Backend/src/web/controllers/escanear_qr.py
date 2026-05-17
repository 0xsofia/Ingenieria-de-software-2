import os
from flask import Flask, Blueprint,request, jsonify
from ...core.models import db
from ...core.services.gestion_asistencias import AsistenciaService

session_bp = Blueprint('generateQR', __name__, url_prefix='/api/generateQR')

@session_bp.route('/api/asistencia/validar', methods=['POST'])
def endpoint_validar_qr():
    data = request.get_json()
    token = data.get('token')
    
    if not token:
        return jsonify({"error": "Token no proporcionado"}), 400

    try:
        mensaje = AsistenciaService.registrar_asistencia_qr(token)
        return jsonify({"message": mensaje}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Error interno del sistema"}), 500