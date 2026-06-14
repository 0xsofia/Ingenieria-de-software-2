from datetime import datetime
from flask import Blueprint, jsonify, request

from src.core.database import db
from src.core.models.profesor import Profesor
from src.core.services.registrarse import validar_telefono

profesor_bp = Blueprint("profesor_bp", __name__, url_prefix="/api/profesor")


@profesor_bp.route("/lista", methods=["GET"])
def obtener_profesores():
    try:
        profesores = Profesor.query.filter_by(is_eliminated=False).all()
        
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

    errors = {}

    if not nombre:
        errors["nombre"] = "El nombre es obligatorio."

    if not dni:
        errors["dni"] = "El DNI es obligatorio."
    elif not dni.isdigit():
        errors["dni"] = "Ingresá el DNI solo con números."

    if not telefono:
        errors["telefono"] = "El teléfono es obligatorio."
    else:
        telefono_normalizado, telefono_error = validar_telefono(telefono)
        if telefono_error is not None:
            errors["telefono"] = telefono_error
        else:
            telefono = telefono_normalizado

    if errors:
        return jsonify({
            "message": "Hay errores de validación en el formulario.",
            "status": "validation_error",
            "errors": errors,
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


@profesor_bp.route("/<int:profesor_id>", methods=["DELETE"])
def eliminar_profesor(profesor_id):
    profesor = Profesor.query.filter_by(profesor_id=profesor_id, is_eliminated=False).first()
    if profesor is None:
        return jsonify({
            "message": "El profesor no existe.",
            "status": "error",
        }), 404

    ahora = datetime.utcnow()
    tiene_clases_futuras = False

    for clase in profesor.clases:
        if clase.fecha is None or clase.horario_inicio is None:
            continue

        inicio_clase = datetime.combine(clase.fecha, clase.horario_inicio)
        if inicio_clase >= ahora:
            tiene_clases_futuras = True
            break

    if tiene_clases_futuras:
        return jsonify({
            "message": "El profesor tiene clases registradas, no se puede eliminar",
            "status": "error",
        }), 409

    profesor.is_eliminated = True
    db.session.commit()

    return jsonify({
        "message": "Profesor eliminado correctamente",
        "status": "ok",
    }), 200
