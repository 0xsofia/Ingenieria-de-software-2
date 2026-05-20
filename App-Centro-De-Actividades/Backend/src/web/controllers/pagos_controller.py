from flask import Blueprint, jsonify, request

from src.core.services.pagos import listar_pagos, listar_pagos_socio

pagos_bp = Blueprint("pagos", __name__, url_prefix="/api/pagos")


@pagos_bp.get("/")
def get_pagos():
    filters = request.args.to_dict(flat=True)
    body, status_code = listar_pagos_socio(filters)
    return jsonify(body), status_code

@pagos_bp.route("/lista", methods=["GET"])
def listar_pagos_controller():
    filters = {
        "dni": request.args.get("dni"),
        "email": request.args.get("email"),
        "nombre": request.args.get("nombre"),
        "fecha_desde": request.args.get("fecha_desde"),
        "fecha_hasta": request.args.get("fecha_hasta"),
    }

    result, status_code = listar_pagos(filters)
    return result, status_code