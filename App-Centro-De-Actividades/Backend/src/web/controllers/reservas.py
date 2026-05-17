from flask import Blueprint, jsonify, request

from src.core.services.reservas import (
    entrar_lista_espera,
    iniciar_reserva_espontanea,
    listar_clases,
    procesar_retorno_pago,
)

reservas_bp = Blueprint("reservas", __name__, url_prefix="/api")


@reservas_bp.get("/clases")
def get_clases():
    body, status_code = listar_clases()
    return jsonify(body), status_code


@reservas_bp.post("/reservas/espontanea")
def reservar_espontanea():
    payload = request.get_json(silent=True) or {}

    clase_id = payload.get("clase_id")
    if clase_id is None:
        return (
            jsonify(
                {
                    "status": "validation_error",
                    "errors": {"clase_id": "La clase es obligatoria."},
                }
            ),
            400,
        )

    try:
        clase_id = int(clase_id)
    except (TypeError, ValueError):
        return (
            jsonify(
                {
                    "status": "validation_error",
                    "errors": {"clase_id": "La clase debe ser un número."},
                }
            ),
            400,
        )

    body, status_code = iniciar_reserva_espontanea(clase_id)
    return jsonify(body), status_code


@reservas_bp.post("/reservas/espontanea/lista-espera")
def waitlist_for_class():
    payload = request.get_json(silent=True) or {}

    clase_id = payload.get("clase_id")
    if clase_id is None:
        return (
            jsonify(
                {
                    "status": "validation_error",
                    "errors": {"clase_id": "La clase es obligatoria."},
                }
            ),
            400,
        )

    try:
        clase_id = int(clase_id)
    except (TypeError, ValueError):
        return (
            jsonify(
                {
                    "status": "validation_error",
                    "errors": {"clase_id": "La clase debe ser un número."},
                }
            ),
            400,
        )

    body, status_code = entrar_lista_espera(clase_id)
    return jsonify(body), status_code


@reservas_bp.post("/reservas/espontanea/pago-retorno")
def payment_return():
    payload = request.get_json(silent=True) or {}

    reserva_id = payload.get("reserva_id")
    status = payload.get("status")

    if reserva_id is None:
        return (
            jsonify(
                {
                    "status": "validation_error",
                    "errors": {"reserva_id": "La reserva es obligatoria."},
                }
            ),
            400,
        )

    try:
        reserva_id = int(reserva_id)
    except (TypeError, ValueError):
        return (
            jsonify(
                {
                    "status": "validation_error",
                    "errors": {"reserva_id": "La reserva debe ser un número."},
                }
            ),
            400,
        )

    body, status_code = procesar_retorno_pago(reserva_id, status)
    return jsonify(body), status_code
