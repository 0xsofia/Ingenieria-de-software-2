from flask import Flask,Blueprint, request, jsonify
from src.core.database import db
from src.core.services.gestion_asistencias import (ReservaNoEncontradaException, 
                            FueraDeHorarioException,
                            generar_token_asistencia) 

generar_token_asistencia_bp = Blueprint('generateQR', __name__, url_prefix='/api/asistencia')

# @generar_token_asistencia_bp.route('/generarQR/<int:reserva_id>', methods=['GET'])
# def endpoint_generar_qr(reserva_id):
#     try:
#         token = generar_token_asistencia(reserva_id)
#         return jsonify({"token": token}), 200
#     except ValueError as e:
#         return jsonify({"error": str(e)}), 403

@generar_token_asistencia_bp.route('/generarQR/<int:reserva_id>', methods=['POST'])
def solicitar_qr(reserva_id):
    try:
        # Invocamos al servicio corregido
        qr_payload = generar_token_asistencia(reserva_id)
        
        return jsonify({
            "status": "allowed",
            "qr_payload": qr_payload
        }), 200
        
    except ReservaNoEncontradaException as e:
        return jsonify({"error": "No encontrado", "message": str(e)}), 404
        
    except FueraDeHorarioException as e:
        # Devuelve 403 para que Axios en el Front reconozca que está fuera de hora pero muestre el mensaje
        return jsonify({
            "error": "Fuera de horario",
            "message": str(e)
        }), 403
        
    except Exception as e:
        # Si sigue fallando algo interno, esto te va a decir la línea exacta en la consola de Flask
        return jsonify({"error": "Error interno del servidor", "message": str(e)}), 500