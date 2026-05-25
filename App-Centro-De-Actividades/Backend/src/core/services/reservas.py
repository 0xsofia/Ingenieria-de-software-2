import calendar
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal
import json
import os
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask_login import current_user
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from src.core.database import db
from src.core.models.clase import Clase
from src.core.models.credito import Credito
from src.core.models.lista_espera import ListaEspera
from src.core.models.pago import Pago
from src.core.models.persona import Socio
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

    existing_pending = existing is not None and existing.estado == "pendiente_pago"

    if existing is not None:
        print(f"existing.estado={existing.estado}")
    print(existing is not None and not existing_pending)

    # Si ya tengo una reserva activa que no esté pendiente de pago, no dejo reservar de nuevo. Si la reserva está pendiente de pago, dejo continuar para intentar cobrar o usar crédito.
    if existing is not None and not existing_pending:
        return {
            "status": "already_reserved",
            "message": "Ya estás reservado en esta clase.",
            "reserva_id": existing.reserva_id,
            "clase_id": clase.clase_id,
        }, 409

    if not existing_pending and _cupo_disponible(clase) <= 0:
        return {
            "status": "no_cupo",
            "message": "La clase se encuentra llena.",
            "clase_id": clase.clase_id,
            "puede_entrar_lista_espera": True,
        }, 409

    credito = _buscar_credito_disponible(socio_id)
    precio = _clase_precio(clase)
    requiere_pago = credito is None and precio is not None and precio > 0

    reserva = existing if existing_pending else Reserva(
        clase_id=clase.clase_id,
        socio_id=socio_id,
        tipo_reserva="espontanea",
        estado="pendiente_pago" if requiere_pago else "confirmada",
        confirmada_en=None if requiere_pago else _now(),
    )

    # hago que si reserva ya existe pero está pendiente de pago, se intente actualizar esa reserva en lugar de crear una nueva. Esto es para evitar que si el usuario tiene un pago pendiente y vuelve a intentar reservar, se le cree una nueva reserva en lugar de usar la existente.
    if existing_pending:
        if requiere_pago:
            reserva.estado = "pendiente_pago"
            reserva.confirmada_en = None
        else:
            reserva.estado = "confirmada"
            reserva.confirmada_en = _now()
    else:
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
            "message": "Usted tiene credito a favor, se omitio el cobro, reserva confirmada",
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


def listar_reservas_socio():
    socio_id, error = _require_socio()
    if error is not None:
        return error

    reservas = (
        Reserva.query.options(joinedload(Reserva.clase))
        .filter(Reserva.socio_id == socio_id)
        .filter(Reserva.estado.in_(sorted(RESERVA_ESTADOS_OCUPAN_CUPO)))
        .order_by(Reserva.creada_en.desc())
        .all()
    )

    if not reservas:
        return {"status": "ok", "reservas": []}, 200

    reserva_ids = [reserva.reserva_id for reserva in reservas]
    pagos = (
        Pago.query.filter(Pago.reserva_id.in_(reserva_ids))
        .order_by(Pago.pago_id.desc())
        .all()
    )
    pagos_por_reserva = {}
    for pago in pagos:
        if pago.reserva_id not in pagos_por_reserva:
            pagos_por_reserva[pago.reserva_id] = pago

    ahora = _now()
    reservas_data = []
    for reserva in reservas:
        clase = reserva.clase
        clase_inicio = _clase_inicio(clase)
        puede_cancelar = _puede_cancelar_reserva(reserva, clase_inicio, ahora)
        pago = pagos_por_reserva.get(reserva.reserva_id)

        print("puede cancelar "+ str(puede_cancelar))

        if pago and pago.estado == "pendiente":
            puede_cancelar = False
            print("ASDFSDFASDFASDFASDFASDFASDFASDFASDFASDFASD: ", reserva.reserva_id, pago.pago_id, pago.estado)

        print("puede cancelar "+ str(puede_cancelar))

        reintegro_estimado = _calcular_reintegro_estimada(pago, clase_inicio, ahora)
        reintegro_aplica = reintegro_estimado is not None

        reservas_data.append(
            {
                "reserva_id": reserva.reserva_id,
                "clase_id": reserva.clase_id,
                "actividad": _clase_actividad_label(clase),
                "fecha": clase.fecha.strftime("%Y-%m-%d") if clase else None,
                "horario_inicio": clase.horario_inicio.strftime("%H:%M") if clase else None,
                "horario_fin": clase.horario_fin.strftime("%H:%M") if clase else None,
                "cancha": clase.cancha if clase else None,
                "estado": reserva.estado,
                "tipo_reserva": reserva.tipo_reserva,
                "precio": float(clase.precio) if clase and clase.precio is not None else None,
                "pago_estado": pago.estado if pago else None,
                "monto_pagado": str(pago.monto_pagado) if pago and pago.monto_pagado is not None else None,
                "puede_cancelar": puede_cancelar,
                "reintegro_aplica": reintegro_aplica,
                "reintegro_estimado": str(reintegro_estimado) if reintegro_estimado is not None else None,
            }
        )

    return {"status": "ok", "reservas": reservas_data}, 200


def cancelar_reserva_espontanea(reserva_id):
    socio_id, error = _require_socio()
    if error is not None:
        return error

    reserva = db.session.get(Reserva, reserva_id)
    if reserva is None or reserva.socio_id != socio_id:
        return {
            "status": "error",
            "message": "La reserva indicada no existe o no te pertenece.",
        }, 404

    if reserva.tipo_reserva != "espontanea":
        return {
            "status": "error",
            "message": "Solo se pueden cancelar reservas espontaneas.",
        }, 409

    if reserva.estado not in RESERVA_ESTADOS_OCUPAN_CUPO:
        return {
            "status": "error",
            "message": "La reserva ya no se encuentra activa.",
        }, 409

    clase = reserva.clase or db.session.get(Clase, reserva.clase_id)
    clase_inicio = _clase_inicio(clase)
    ahora = _now()
    if clase_inicio is None:
        return {
            "status": "error",
            "message": "No se pudo identificar la clase asociada a la reserva.",
        }, 409

    if clase_inicio <= ahora:
        return {
            "status": "error",
            "message": "La clase ya comenzo o finalizo, no puede cancelarse.",
        }, 409

    pago = (
        Pago.query.filter_by(reserva_id=reserva.reserva_id)
        .order_by(Pago.pago_id.desc())
        .first()
    )

    reintegro_info = {
        "aplica": False,
        "estado": "no_aplica",
        "monto": None,
        "message": None,
    }
    reintegro_monto = _calcular_reintegro_estimada(pago, clase_inicio, ahora)

    if reintegro_monto is not None:
        reintegro_info["aplica"] = True
        reintegro_info["monto"] = str(reintegro_monto)

        estado_reintegro, mensaje_reintegro = _reintegrar_mercadopago(
            pago=pago,
            monto=reintegro_monto,
        )
        reintegro_info["estado"] = estado_reintegro
        reintegro_info["message"] = mensaje_reintegro
    elif pago is not None and not _pago_aprobado(pago):
        pago.estado = "cancelado"

    credito = Credito.query.filter_by(reserva_que_consume_id=reserva.reserva_id).first()
    if credito is not None:
        credito.reserva_que_consume_id = None
        credito.consumido_en = None
        credito.estado = "disponible"

    reserva.estado = "cancelada"
    reserva.cancelada_en = ahora

    db.session.flush()

    cancelaciones_mes = _contar_cancelaciones_mes(socio_id, ahora)
    sancion_aplicada = cancelaciones_mes > 3
    descuento_bloqueado_hasta = None

    if sancion_aplicada:
        socio = db.session.get(Socio, socio_id)
        if socio is not None:
            descuento_bloqueado_hasta = _fin_mes_siguiente(ahora)
            socio.descuento_bloqueado_hasta = descuento_bloqueado_hasta

    db.session.commit()

    reintegro_aplica = reintegro_info["aplica"]
    if reintegro_aplica and not sancion_aplicada:
        scenario_code = "escenario_1"
        scenario_message = "Escenario 1: cancelacion con devolucion del 50% y sin sancion."
    elif not reintegro_aplica and not sancion_aplicada:
        scenario_code = "escenario_2"
        scenario_message = "Escenario 2: cancelacion sin devolucion del 50% y sin sancion."
    elif reintegro_aplica and sancion_aplicada:
        scenario_code = "escenario_3"
        scenario_message = "Escenario 3: cancelacion con devolucion del 50% y con sancion."
    else:
        scenario_code = "escenario_4"
        scenario_message = "Escenario 4: cancelacion sin devolucion del 50% y con sancion."

    return {
        "status": "cancelled",
        "message": "La reserva fue cancelada correctamente.",
        "scenario": scenario_code,
        "scenario_message": scenario_message,
        "reserva_id": reserva.reserva_id,
        "reintegro": reintegro_info,
        "cancelaciones_mes": cancelaciones_mes,
        "sancion_aplicada": sancion_aplicada,
        "descuento_bloqueado_hasta": descuento_bloqueado_hasta.isoformat()
        if descuento_bloqueado_hasta is not None
        else None,
    }, 200


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

        init_point =  preference.get("sandbox_init_point")
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


def _clase_inicio(clase):
    if clase is None:
        return None

    return datetime.combine(clase.fecha, clase.horario_inicio).replace(tzinfo=timezone.utc)


def _puede_cancelar_reserva(reserva, clase_inicio, ahora):
    if reserva is None or clase_inicio is None:
        print("1")
        return False


    if reserva.estado not in RESERVA_ESTADOS_OCUPAN_CUPO:
        print("2")
        return False

    print("clase_inicio > ahora: "+ str(clase_inicio > ahora))
    return clase_inicio > ahora


def _calcular_reintegro_estimada(pago, clase_inicio, ahora):
    if pago is None or clase_inicio is None:
        return None

    if not _pago_aprobado(pago):
        return None

    if clase_inicio - ahora <= timedelta(hours=48):
        return None

    monto_base = _monto_base_pago(pago)
    if monto_base is None or monto_base <= 0:
        return None

    return (monto_base * Decimal("0.50")).quantize(Decimal("0.01"))


def _monto_base_pago(pago):
    if pago is None:
        return None

    base = pago.monto_pagado if pago.monto_pagado is not None else pago.monto_bruto
    if base is None:
        return None

    return Decimal(str(base))


def _pago_aprobado(pago):
    estado = (getattr(pago, "estado", "") or "").strip().lower()
    return estado in {"aprobado", "approved"}


def _contar_cancelaciones_mes(socio_id, ahora):
    inicio_mes = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    year = ahora.year + (1 if ahora.month == 12 else 0)
    month = 1 if ahora.month == 12 else ahora.month + 1
    inicio_mes_siguiente = inicio_mes.replace(year=year, month=month)

    return (
        Reserva.query.filter_by(socio_id=socio_id, estado="cancelada")
        .filter(Reserva.cancelada_en >= inicio_mes)
        .filter(Reserva.cancelada_en < inicio_mes_siguiente)
        .count()
    )


def _fin_mes_siguiente(ahora):
    year = ahora.year + (1 if ahora.month == 12 else 0)
    month = 1 if ahora.month == 12 else ahora.month + 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, last_day)


def _reintegrar_mercadopago(pago, monto):
    if pago is None:
        return "no_aplica", "No se encontro un pago aprobado para reintegrar."

    access_token = (os.environ.get("MP_ACCESS_TOKEN") or "").strip()
    if not access_token:
        pago.estado = "reintegro_pendiente"
        return "pendiente", "No se configuro MP_ACCESS_TOKEN para el reintegro."

    payment_id = _buscar_pago_mp_id(pago.external_ref, access_token)
    if payment_id is None:
        pago.estado = "reintegro_fallido"
        return "fallido", "No se encontro el pago en Mercado Pago."

    idempotency_key = _build_refund_idempotency_key(pago, monto)
    refund_ok, refund_error = _crear_reintegro_mp(payment_id, monto, access_token, idempotency_key)
    if not refund_ok:
        pago.estado = "reintegro_fallido"
        detalle = f" Detalle: {refund_error}" if refund_error else ""
        return "fallido", f"No se pudo completar el reintegro en Mercado Pago.{detalle}"

    pago.estado = "reintegrado_parcial"
    return "reintegrado", "Reintegro parcial iniciado en Mercado Pago."


def _buscar_pago_mp_id(external_ref, access_token):
    if not external_ref:
        return None

    query = urlencode({"external_reference": external_ref})
    url = f"https://api.mercadopago.com/v1/payments/search?{query}"

    try:
        request = Request(
            url,
            headers={"Authorization": f"Bearer {access_token}"},
            method="GET",
        )
        with urlopen(request, timeout=10) as response:
            raw = response.read().decode("utf-8")
            payload = json.loads(raw)
    except HTTPError as exc:
        try:
            body = exc.read().decode("utf-8")
        except Exception:
            body = ""
        print("Mercado Pago search failed:", exc.code, body)
        return None
    except (URLError, ValueError, OSError) as exc:
        print("Mercado Pago search failed:", str(exc))
        return None

    results = payload.get("results") or []
    if not results:
        return None

    # Prefer approved payments if available.
    approved = next((item for item in results if str(item.get("status")).lower() == "approved"), None)
    chosen = approved or results[0]
    return chosen.get("id")


def _crear_reintegro_mp(payment_id, monto, access_token, idempotency_key=None):
    if payment_id is None:
        return False, "payment_id invalido"

    payload = {"amount": float(monto)} if monto is not None else {}
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

    if idempotency_key:
        headers["X-Idempotency-Key"] = idempotency_key

    print("Iniciando reintegro en Mercado Pago", {"payment_id": payment_id, "monto": monto, "idempotency_key": idempotency_key})

    try:
        request = Request(
            f"https://api.mercadopago.com/v1/payments/{payment_id}/refunds",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urlopen(request, timeout=10) as response:
            response.read()
        return True, None
    except HTTPError as exc:
        try:
            body = exc.read().decode("utf-8")
        except Exception:
            body = ""
        print("Mercado Pago refund failed:", exc.code, body)
        return False, body
    except (URLError, ValueError, OSError) as exc:
        print("Mercado Pago refund failed:", str(exc))
        return False, str(exc)


def _build_refund_idempotency_key(pago, monto):
    if pago is None:
        return None

    parts = ["refund"]

    if pago.reserva_id is not None:
        parts.append(str(pago.reserva_id))

    if pago.pago_id is not None:
        parts.append(str(pago.pago_id))

    if monto is not None:
        parts.append(str(monto))

    if len(parts) == 1 and pago.external_ref:
        parts.append(str(pago.external_ref))

    if len(parts) == 1:
        parts.append(str(uuid.uuid4()))

    return "-".join(parts)


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
