from flask import Blueprint, request, jsonify
from src.core.services.gestion_asistencias import (
    AccesoQRDenegadoException,
    AsistenciaYaRegistradaException,
    AutenticacionRequeridaException,
    QRInvalidoException,
    ReservaNoEncontradaException,
    registrar_asistencia,
    registrar_asistencia_manual,
)

escanearQR_bp = Blueprint('scanQR', __name__, url_prefix='/api/asistencia')

# @escanearQR_bp.post('/escanearQR')
# def endpoint_escanear_qr():
#     data = request.get_json()

#     # Validación de formato del transporte (Responsabilidad del Controlador)
#     if not data or 'dni' not in data or 'id_reserva' not in data:
#         return jsonify({"error": "El QR es inválido."}), 400

#     dni = data.get('dni')
#     id_reserva_raw = data.get('id_reserva')

#     try:
#         id_reserva = int(id_reserva_raw)
#     except (ValueError, TypeError):
#         return jsonify({"error": "El QR es inválido."}), 400

#     try:
#         # El controlador delega el negocio al servicio de asistencia
#         mensaje_exito = registrar_asistencia(dni, id_reserva)
#         return jsonify({
#             "status": "success",
#             "message": mensaje_exito
#         }), 200
        
#     except ClienteNoAsociadoException as e:
#         return jsonify({
#             "error": "No registrado",
#             "message": str(e)
#         }), 404
        
#     except AsistenciaYaRegistradaException as e:
#         return jsonify({
#             "error": "Ya escaneado",
#             "message": str(e)
#         }), 409
        
#     except Exception as e:
#         return jsonify({"error": "Error interno del servidor", "message": str(e)}), 500

@escanearQR_bp.post('/escanearQR')
def endpoint_escanear_qr():
    data = request.get_json()

    # Validación de formato del transporte básico obligatorio
    if not data or 'dni' not in data or 'id_reserva' not in data:
        return jsonify({"error": "El QR es inválido."}), 400

    dni = data.get('dni')
    id_reserva_raw = data.get('id_reserva')
    id_clase_raw = data.get('id_clase')

    try:
        id_reserva = int(id_reserva_raw)
    except (ValueError, TypeError):
        return jsonify({"error": "El QR es inválido."}), 400

    id_clase = None
    if id_clase_raw is not None:
        try:
            id_clase = int(id_clase_raw)
        except (ValueError, TypeError):
            return jsonify({
                "error": "QR inválido",
                "message": "El identificador de clase provisto es inválido.",
            }), 400

    try:
        mensaje_exito = registrar_asistencia(dni, id_reserva, id_clase)
        return jsonify({
            "status": "success",
            "message": mensaje_exito
        }), 200

    except AutenticacionRequeridaException as e:
        return jsonify({
            "error": "No autenticado",
            "message": str(e)
        }), 401

    except AccesoQRDenegadoException as e:
        return jsonify({
            "error": "Acceso denegado",
            "message": str(e)
        }), 403

    except QRInvalidoException as e:
        return jsonify({
            "error": "QR inválido",
            "message": str(e)
        }), 400

    except ReservaNoEncontradaException as e:
        return jsonify({
            "error": "No encontrado",
            "message": str(e)
        }), 404

    except AsistenciaYaRegistradaException as e:
        return jsonify({
            "error": "Ya escaneado",
            "message": str(e)
        }), 409
        
    except Exception as e:
        return jsonify({"error": "Error interno del servidor", "message": str(e)}), 500


@escanearQR_bp.post('/registrar-manual/<int:reserva_id>')
def endpoint_registrar_asistencia_manual(reserva_id):
    """Endpoint para que los empleados registren asistencia manualmente."""
    try:
        mensaje_exito = registrar_asistencia_manual(reserva_id)
        return jsonify({
            "status": "success",
            "message": mensaje_exito
        }), 200

    except AutenticacionRequeridaException as e:
        return jsonify({
            "error": "No autenticado",
            "message": str(e)
        }), 401

    except AccesoQRDenegadoException as e:
        return jsonify({
            "error": "Acceso denegado",
            "message": str(e)
        }), 403

    except ReservaNoEncontradaException as e:
        return jsonify({
            "error": "No encontrado",
            "message": str(e)
        }), 404

    except AsistenciaYaRegistradaException as e:
        return jsonify({
            "error": "Ya registrado",
            "message": str(e)
        }), 409
        
    except Exception as e:
        return jsonify({"error": "Error interno del servidor", "message": str(e)}), 500
