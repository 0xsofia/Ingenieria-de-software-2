from flask import Blueprint, jsonify, request

from src.core.database import db
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


@profesor_bp.route("/crear", methods=["POST"])
def crear_profesor():
    payload = request.get_json(silent=True) or {}
    nombre = (payload.get("nombre") or "").strip()
    dni = (payload.get("dni") or "").strip()
    telefono = (payload.get("telefono") or "").strip()

    if not nombre or not dni or not telefono:
        return jsonify({
            "message": "Todos los campos son obligatorios.",
            "status": "validation_error",
            "errors": {
                **({"nombre": "El nombre es obligatorio."} if not nombre else {}),
                **({"dni": "El DNI es obligatorio."} if not dni else {}),
                **({"telefono": "El teléfono es obligatorio."} if not telefono else {}),
            },
        }), 400

    profesor_existente = Profesor.query.filter_by(dni=dni).first()
    if profesor_existente:
        return jsonify({
            "message": "El profesor fue registrado anteriormente",
            "status": "validation_error",
        }), 400

    profesor = Profesor(nombre=nombre, dni=dni, telefono=telefono)
    db.session.add(profesor)
    db.session.commit()

    return jsonify({
        "message": "El profesor fue cargado correctamente",
        "profesor": {
            "id": profesor.profesor_id,
            "nombre": profesor.nombre,
            "dni": profesor.dni,
            "telefono": profesor.telefono,
        },
    }), 201
