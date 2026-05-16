from flask import Blueprint, request, jsonify

from src.core.services.clase_service import ClaseService

clase_bp = Blueprint("clase_bp", __name__, url_prefix="/api/clase")


@clase_bp.route("/crear", methods=["POST"])
def crear_clase():

    data = request.get_json()
    print("Datos recibidos para crear clase:", data)  # Debug: Verificar datos recibidos
    try:

        clase = ClaseService.crear_clase(data)

        return jsonify({
            "message": "La clase fue registrada correctamente",
            "id": clase.clase_id
        }), 201

    except Exception as e:
        print("Error al crear clase:", str(e))  # Debug: Verificar error específico
        return jsonify({
            "error": str(e)
        }), 400