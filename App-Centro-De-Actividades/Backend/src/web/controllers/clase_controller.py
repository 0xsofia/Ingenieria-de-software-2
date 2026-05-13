from flask import Blueprint, request, jsonify

from src.core.services.clase_service import ClaseService

clase_bp = Blueprint("clase_bp", __name__, url_prefix="/api/clase")


@clase_bp.route("/crear", methods=["POST"])
def crear_clase():

    data = request.get_json()

    try:

        clase = ClaseService.crear_clase(data)

        return jsonify({
            "message": "La clase fue registrada correctamente",
            "id": clase.id
        }), 201

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 400