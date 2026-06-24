from flask import Blueprint, jsonify, request
from src.core.services.metricas_service import obtener_dashboard_metricas

metricas_bp = Blueprint('metricas', __name__, url_prefix='/api/metricas')

@metricas_bp.route('', methods=['GET'])
@metricas_bp.route('/', methods=['GET'])
def get_metrica():
    try:
        anio_sel = request.args.get('anio')
        mes_sel = request.args.get('mes')
        
        data = obtener_dashboard_metricas(anio=anio_sel, mes=mes_sel)
        return jsonify({
            "status": "success",
            "data": data
        }), 200
    except Exception as e:
        import traceback
        print("\n❌ ERROR CRÍTICO EN MÉTRICAS:")
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
