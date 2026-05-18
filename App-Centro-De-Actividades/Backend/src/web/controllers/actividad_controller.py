from flask import Blueprint, jsonify

from src.core.services.actividad_service import ActividadService

actividad_bp = Blueprint('actividad_bp', __name__, url_prefix='/api/actividades')


@actividad_bp.get('')
def listar_actividades():
    actividades = ActividadService.obtener_actividades()

    return jsonify(
        {
            'status': 'ok',
            'actividades': [
                {
                    'actividad_id': actividad.actividad_id,
                    'nombre': actividad.nombre,
                }
                for actividad in actividades
            ],
        }
    ), 200
