from flask import Blueprint, jsonify, request

from src.core.services.pagos import listar_pagos_socio

pagos_bp = Blueprint("pagos", __name__, url_prefix="/api/pagos")


@pagos_bp.get("/")
def get_pagos():
    filters = request.args.to_dict(flat=True)
    body, status_code = listar_pagos_socio(filters)
    return jsonify(body), status_code
