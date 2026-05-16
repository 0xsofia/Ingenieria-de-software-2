from flask import Blueprint, jsonify

from src.core.models.profesor import Profesor

profesor_bp = Blueprint("profesor_bp", __name__, url_prefix="/api/profesor")


@profesor_bp.route("/lista", methods=["GET"])
def obtener_profesores():
    try:
        profesores = Profesor.query.all()
        
        profesores_data = [
            {
                "id": profesor.profesor_id,
                "nombre": profesor.nombre,
                "dni": profesor.dni,
                "telefono": profesor.telefono
            }
            for profesor in profesores
        ]
        
        return jsonify(profesores_data), 200
    
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 400
