from datetime import datetime, timezone
import json
import os
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask_login import current_user
from sqlalchemy.exc import IntegrityError

from src.core.database import db
from src.core.models.clase import Clase
from src.core.models.credito import Credito
from src.core.models.lista_espera import ListaEspera
from src.core.models.pago import Pago
from src.core.models.reserva import Reserva


RESERVA_ESTADOS_OCUPAN_CUPO = {"pendiente_pago", "confirmada"}


def iniciar_reserva_espontanea(clase_id):
    socio_id, error = _require_socio()
    if error is not None:
        return error

    clase = db.session.get(Clase, clase_id)
    if clase is None:
        return {
            "status": "error",
            "message": "La clase seleccionada no existe.",
        }, 404

    if _clase_estado(clase) != "activa":
        return {
            "status": "error",
            "message": "La clase seleccionada no está disponible para reservas.",
        }, 409

    existing = (
        Reserva.query.filter_by(clase_id=clase.clase_id, socio_id=socio_id)
        .filter(Reserva.estado.in_(sorted(RESERVA_ESTADOS_OCUPAN_CUPO)))
        .order_by(Reserva.reserva_id.desc())
        .first()
    )
    if existing is not None:
        return {
            "status": "already_reserved",
            "message": "Ya estás reservado en esta clase.",
            "reserva_id": existing.reserva_id,
            "clase_id": clase.clase_id,
        }, 409

    if _cupo_disponible(clase) <= 0:
        return {
            "status": "no_cupo",
            "message": "No hay más cupo en la clase seleccionada.",
            "clase_id": clase.clase_id,
            "puede_entrar_lista_espera": True,
        }, 409

    credito = _buscar_credito_disponible(socio_id)
    precio = _clase_precio(clase)
    requiere_pago = credito is None and precio is not None and precio > 0

    reserva = Reserva(
        clase_id=clase.clase_id,
        socio_id=socio_id,
        tipo_reserva="espontanea",
        estado="pendiente_pago" if requiere_pago else "confirmada",
        confirmada_en=None if requiere_pago else _now(),
    )

    db.session.add(reserva)
    try:
        db.session.flush()
    except IntegrityError:
        db.session.rollback()
        return {
            "status": "already_reserved",
            "message": "Ya estás reservado en esta clase.",
            "clase_id": clase.clase_id,
        }, 409

    if credito:
        credito.reserva_que_consume_id = reserva.reserva_id
        credito.consumido_en = _now()
        credito.estado = "consumido"
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return {
                "status": "already_reserved",
                "message": "Ya estás reservado en esta clase.",
                "clase_id": clase.clase_id,
            }, 409

        return {
            "status": "reserved",
            "message": "Reserva confirmada usando crédito a favor.",
            "reserva_id": reserva.reserva_id,
            "payment_required": False,
        }, 200

    if not requiere_pago:
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return {
                "status": "already_reserved",
                "message": "Ya estás reservado en esta clase.",
                "clase_id": clase.clase_id,
            }, 409

        return {
            "status": "reserved",
            "message": "Reserva confirmada.",
            "reserva_id": reserva.reserva_id,
            "payment_required": False,
        }, 200

    pago = Pago(
        socio_id=socio_id,
        reserva_id=reserva.reserva_id,
        proveedor="mercadopago",
        external_ref=str(uuid.uuid4()),
        monto_bruto=precio,
        descuento_pct=0,
        estado="pendiente",
    )
    db.session.add(pago)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {
            "status": "already_reserved",
            "message": "Ya estás reservado en esta clase.",
            "clase_id": clase.clase_id,
        }, 409

    payment_url = _crear_checkout_mercadopago(pago=pago, reserva=reserva, clase=clase)

    if payment_url is None:
        pago.estado = "error"
        db.session.commit()

        return {
            "status": "error",
            "message": "No pudimos iniciar el pago en Mercado Pago. Verificá el MP_ACCESS_TOKEN y la conexión.",
            "reserva_id": reserva.reserva_id,
            "pago_id": pago.pago_id,
        }, 502

    return {
        "status": "payment_required",
        "message": "Redirigiendo a Mercado Pago para completar el pago.",
        "reserva_id": reserva.reserva_id,
        "pago_id": pago.pago_id,
        "payment_required": True,
        "payment_url": payment_url,
    }, 200


def entrar_lista_espera(clase_id):
    socio_id, error = _require_socio()
    if error is not None:
        return error

    clase = db.session.get(Clase, clase_id)
    if clase is None:
        return {
            "status": "error",
            "message": "La clase seleccionada no existe.",
        }, 404

    existing = (
        ListaEspera.query.filter_by(clase_id=clase_id, socio_id=socio_id)
        .filter(ListaEspera.estado != "cancelada")
        .first()
    )
    if existing is not None:
        return {
            "status": "ok",
            "message": "Ya estás anotado en la lista de espera para esta clase.",
            "lista_espera_id": existing.lista_espera_id,
            "posicion": existing.posicion,
        }, 200

    max_position = (
        db.session.query(db.func.max(ListaEspera.posicion))
        .filter_by(clase_id=clase_id)
        .scalar()
        or 0
    )

    entry = ListaEspera(
        clase_id=clase_id,
        socio_id=socio_id,
        posicion=max_position + 1,
        estado="pendiente",
    )
    db.session.add(entry)
    db.session.commit()

    return {
        "status": "waitlisted",
        "message": "Te anotamos en la lista de espera para la clase seleccionada.",
        "lista_espera_id": entry.lista_espera_id,
        "posicion": entry.posicion,
    }, 200


def procesar_retorno_pago(reserva_id, pago_status):
    socio_id, error = _require_socio()
    if error is not None:
        return error

    reserva = db.session.get(Reserva, reserva_id)
    if reserva is None or reserva.socio_id != socio_id:
        return {
            "status": "error",
            "message": "La reserva indicada no existe o no te pertenece.",
        }, 404

    pago = Pago.query.filter_by(reserva_id=reserva.reserva_id).order_by(Pago.pago_id.desc()).first()
    if pago is None:
        return {
            "status": "error",
            "message": "No se encontró un pago asociado a la reserva.",
        }, 409

    normalized = (pago_status or "").strip().lower()

    if reserva.estado == "confirmada":
        return {
            "status": "reserved",
            "message": "La reserva ya estaba confirmada.",
            "reserva_id": reserva.reserva_id,
        }, 200

    if normalized in {"approved", "aprobado", "success"}:
        reserva.estado = "confirmada"
        reserva.confirmada_en = _now()

        pago.estado = "aprobado"
        pago.fecha_pago = _now()
        pago.monto_pagado = pago.monto_bruto

        db.session.commit()

        return {
            "status": "reserved",
            "message": "Pago aprobado. Te inscribimos en la clase.",
            "reserva_id": reserva.reserva_id,
        }, 200

    if normalized in {"pending", "in_process"}:
        return {
            "status": "payment_pending",
            "message": "El pago quedó pendiente. Cuando se acredite, se confirmará la inscripción.",
            "reserva_id": reserva.reserva_id,
        }, 200

    reserva.estado = "pago_fallido"
    pago.estado = "rechazado"
    db.session.commit()

    return {
        "status": "payment_failed",
        "message": "No se pudo realizar la inscripción por un error de pago.",
        "reserva_id": reserva.reserva_id,
    }, 402


def _require_socio():
    if not current_user.is_authenticated:
        return None, ({"status": "error", "message": "Debes iniciar sesión."}, 401)

    if getattr(current_user, "role", None) != "socio":
        return None, (
            {
                "status": "error",
                "message": "Solo los socios pueden realizar reservas.",
            },
            403,
        )

    return current_user.persona_id, None


def _cupo_disponible(clase):
    ocupados = (
        db.session.query(db.func.count(Reserva.reserva_id))
        .filter(Reserva.clase_id == clase.clase_id)
        .filter(Reserva.estado.in_(sorted(RESERVA_ESTADOS_OCUPAN_CUPO)))
        .scalar()
        or 0
    )

    return max(int(clase.cupos) - int(ocupados), 0)


def _buscar_credito_disponible(socio_id):
    return (
        Credito.query.filter_by(socio_id=socio_id)
        .filter(Credito.reserva_que_consume_id.is_(None))
        .filter(Credito.consumido_en.is_(None))
        .filter(db.func.lower(Credito.estado) == "disponible")
        .order_by(Credito.otorgado_en.asc())
        .first()
    )


def _crear_checkout_mercadopago(pago, reserva, clase):
    frontend_base = (os.environ.get("FRONTEND_BASE_URL") or "http://localhost:5173").rstrip("/")

    return_urls = {
        "success": f"{frontend_base}/pago/retorno?status=approved&reserva_id={reserva.reserva_id}",
        "failure": f"{frontend_base}/pago/retorno?status=failure&reserva_id={reserva.reserva_id}",
        "pending": f"{frontend_base}/pago/retorno?status=pending&reserva_id={reserva.reserva_id}",
    }

    access_token = (os.environ.get("MP_ACCESS_TOKEN") or "").strip()
    if not access_token:
        return return_urls["pending"]

    preference_payload = {
        "items": [
            {
                "title": f"Clase {_clase_actividad_label(clase)}",
                "quantity": 1,
                "currency_id": "ARS",
                "unit_price": float(pago.monto_bruto),
            }
        ],
        "external_reference": pago.external_ref,
        "back_urls": return_urls,
    }

    if frontend_base.startswith("https://"):
        preference_payload["auto_return"] = "approved"

    try:
        request = Request(
            "https://api.mercadopago.com/checkout/preferences",
            data=json.dumps(preference_payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
            method="POST",
        )

        with urlopen(request, timeout=10) as response:
            raw = response.read().decode("utf-8")
            preference = json.loads(raw)

        init_point = preference.get("init_point") or preference.get("sandbox_init_point")
        if init_point:
            return init_point

    except HTTPError as exc:
        # Token inválido / permisos / payload inválido.
        try:
            body = exc.read().decode("utf-8")
        except Exception:
            body = ""
        print("Mercado Pago preference error:", exc.code, body)
        return None

    except (URLError, ValueError, OSError) as exc:
        print("Mercado Pago preference request failed:", str(exc))
        return None


def _now():
    return datetime.now(timezone.utc)


def _clase_estado(clase):
    return (getattr(clase, "estado", "activa") or "activa").strip().lower()


def _clase_precio(clase):
    precio = getattr(clase, "precio", None)
    if precio is None:
        return None

    try:
        return float(precio)
    except (TypeError, ValueError):
        return None


def _clase_actividad_label(clase):
    actividad = getattr(clase, "actividad", None)

    if actividad is None:
        return "actividad"

    return getattr(actividad, "value", getattr(actividad, "nombre", str(actividad)))
