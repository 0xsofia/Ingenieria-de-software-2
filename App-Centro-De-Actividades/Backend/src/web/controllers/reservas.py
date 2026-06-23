from flask import Blueprint, jsonify, request

from src.core.services.reservas import (
    cancelar_reserva_abonada,
    cancelar_reserva_espontanea,
    entrar_lista_espera,
    iniciar_reserva_abonada,
    iniciar_reserva_espontanea,
    listar_reservas_socio,
    listar_abonos_mensuales_socio,
    renovar_abono_mensual,
    cancelar_abono_mensual,
    procesar_retorno_pago,
    obtener_ofertas_activas,
    confirmar_turno,
    abandonar_lista_espera,
)


reservas_bp = Blueprint("reservas", __name__, url_prefix="/api")


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


@reservas_bp.post("/reservas/abonada")
def reservar_abonada():
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

    body, status_code = iniciar_reserva_abonada(clase_id)
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
    payment_id = payload.get("payment_id") or payload.get("collection_id")
    external_reference = payload.get("external_reference")

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

    body, status_code = procesar_retorno_pago(
        reserva_id,
        status,
        payment_id=payment_id,
        external_reference=external_reference,
    )
    return jsonify(body), status_code


@reservas_bp.get("/reservas/mis-clases")
def listar_mis_clases():
    body, status_code = listar_reservas_socio()
    return jsonify(body), status_code


@reservas_bp.get("/reservas/mis-abonos")
def listar_mis_abonos():
    body, status_code = listar_abonos_mensuales_socio()
    return jsonify(body), status_code


@reservas_bp.post("/reservas/abonos/renovar")
def renovar_abono():
    payload = request.get_json(silent=True) or {}

    abono_id = payload.get("abono_mensual_id")
    if abono_id is None:
        return (
            jsonify(
                {
                    "status": "validation_error",
                    "errors": {"abono_mensual_id": "El id del abono mensual es obligatorio."},
                }
            ),
            400,
        )

    try:
        abono_id = int(abono_id)
    except (TypeError, ValueError):
        return (
            jsonify(
                {
                    "status": "validation_error",
                    "errors": {"abono_mensual_id": "El id debe ser un número."},
                }
            ),
            400,
        )

    body, status_code = renovar_abono_mensual(abono_id)
    return jsonify(body), status_code


@reservas_bp.post("/reservas/abonos/cancelar")
def cancelar_abono():
    payload = request.get_json(silent=True) or {}

    abono_id = payload.get("abono_mensual_id")
    if abono_id is None:
        return (
            jsonify(
                {
                    "status": "validation_error",
                    "errors": {"abono_mensual_id": "El id del abono mensual es obligatorio."},
                }
            ),
            400,
        )

    try:
        abono_id = int(abono_id)
    except (TypeError, ValueError):
        return (
            jsonify(
                {
                    "status": "validation_error",
                    "errors": {"abono_mensual_id": "El id debe ser un número."},
                }
            ),
            400,
        )

    body, status_code = cancelar_abono_mensual(abono_id)
    return jsonify(body), status_code


@reservas_bp.post("/reservas/espontanea/cancelar")
def cancelar_reserva():
    payload = request.get_json(silent=True) or {}

    reserva_id = payload.get("reserva_id")
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
                    "errors": {"reserva_id": "La reserva debe ser un numero."},
                }
            ),
            400,
        )

    body, status_code = cancelar_reserva_espontanea(reserva_id)
    return jsonify(body), status_code


@reservas_bp.post("/reservas/abonada/cancelar")
def cancelar_reserva_abonada_route():
    payload = request.get_json(silent=True) or {}

    reserva_id = payload.get("reserva_id")
    confirmar_sancion = bool(payload.get("confirmar_sancion", False))
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
                    "errors": {"reserva_id": "La reserva debe ser un numero."},
                }
            ),
            400,
        )

    body, status_code = cancelar_reserva_abonada(
        reserva_id,
        confirmar_sancion=confirmar_sancion,
    )
    return jsonify(body), status_code


@reservas_bp.get('/reservas/ofertas-activas')
def ofertas_activas():
    body, status_code = obtener_ofertas_activas()
    return jsonify(body), status_code


@reservas_bp.post('/reservas/confirmar')
def confirmar_oferta():
    payload = request.get_json(silent=True) or {}

    lista_espera_id = payload.get('lista_espera_id')
    if lista_espera_id is None:
        return (
            jsonify(
                {
                    'status': 'validation_error',
                    'errors': {'lista_espera_id': 'El id de la lista de espera es obligatorio.'},
                }
            ),
            400,
        )

    try:
        lista_espera_id = int(lista_espera_id)
    except (TypeError, ValueError):
        return (
            jsonify(
                {
                    'status': 'validation_error',
                    'errors': {'lista_espera_id': 'El id debe ser un número.'},
                }
            ),
            400,
        )

    body, status_code = confirmar_turno(lista_espera_id)
    return jsonify(body), status_code


@reservas_bp.post('/reservas/lista-espera/abandonar')
def abandonar_lista_espera_route():
    payload = request.get_json(silent=True) or {}

    lista_espera_id = payload.get('lista_espera_id')
    if lista_espera_id is None:
        return (
            jsonify(
                {
                    'status': 'validation_error',
                    'errors': {'lista_espera_id': 'El id de la lista de espera es obligatorio.'},
                }
            ),
            400,
        )

    try:
        lista_espera_id = int(lista_espera_id)
    except (TypeError, ValueError):
        return (
            jsonify(
                {
                    'status': 'validation_error',
                    'errors': {'lista_espera_id': 'El id debe ser un número.'},
                }
            ),
            400,
        )

    body, status_code = abandonar_lista_espera(lista_espera_id)
    return jsonify(body), status_code
