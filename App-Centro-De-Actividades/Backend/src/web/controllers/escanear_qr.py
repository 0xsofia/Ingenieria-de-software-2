from flask import Flask, Blueprint,request, jsonify
from src.core.services.gestion_asistencias import ( registrar_asistencia, 
                                                    ClienteNoAsociadoException,
                                                    AsistenciaYaRegistradaException)

escanearQR_bp = Blueprint('scanQR', __name__, url_prefix='/api/asistencia')

@escanearQR_bp.post('/escanearQR')
def endpoint_escanear_qr():
    data = request.get_json()

    # Validación de formato del transporte (Responsabilidad del Controlador)
    if not data or 'dni' not in data or 'id_reserva' not in data:
        return jsonify({"error": "El QR es inválido."}), 400

    dni = data.get('dni')
    id_reserva_raw = data.get('id_reserva')

    try:
        id_reserva = int(id_reserva_raw)
    except (ValueError, TypeError):
        return jsonify({"error": "El QR es inválido."}), 400

    try:
        # El controlador delega el negocio al servicio de asistencia
        mensaje_exito = registrar_asistencia(dni, id_reserva)
        return jsonify({
            "status": "success",
            "message": mensaje_exito
        }), 200
        
    except ClienteNoAsociadoException as e:
        return jsonify({
            "error": "No registrado",
            "message": str(e)
        }), 404
        
    except AsistenciaYaRegistradaException as e:
        return jsonify({
            "error": "Ya escaneado",
            "message": str(e)
        }), 409
        
    except Exception as e:
        return jsonify({"error": "Error interno del servidor", "message": str(e)}), 500

