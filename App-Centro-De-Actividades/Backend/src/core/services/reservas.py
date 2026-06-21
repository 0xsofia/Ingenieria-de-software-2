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
from src.core.models.abono_mensual import AbonoMensual
from src.core.models.actividad import Actividad
from src.core.models.clase import Clase
from src.core.models.credito import Credito
from src.core.models.lista_espera import ListaEspera
from src.core.models.pago import Pago
from src.core.models.persona import Socio
from src.core.models.reserva import Reserva
from src.core.models.abono_mensual import AbonoMensual
from src.core.models.actividad import Actividad
from src.core.services import telegram


RESERVA_ESTADOS_OCUPAN_CUPO = {"pendiente_pago", "confirmada"}
CLASES_POR_ABONO = 4
DESCUENTO_ABONO_PCT = Decimal("20.00")


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


def iniciar_reserva_abonada(clase_id):
    socio_id, error = _require_socio()
    if error is not None:
        return error

    clase_base = db.session.get(Clase, clase_id)
    if clase_base is None:
        return {
            "status": "error",
            "message": "La clase seleccionada no existe.",
        }, 404

    if _clase_estado(clase_base) != "activa":
        return {
            "status": "error",
            "message": "La clase seleccionada no está disponible para reservas.",
        }, 409

    clases_abono = _buscar_clases_consecutivas(clase_base)
    if len(clases_abono) != CLASES_POR_ABONO:
        return {
            "status": "no_cupo",
            "message": "No se puede realizar la reserva abonada porque no existen las 4 clases consecutivas en ese día y horario.",
            "clase_id": clase_base.clase_id,
        }, 409

    for clase in clases_abono:
        if _cupo_disponible(clase) <= 0:
            return {
                "status": "no_cupo",
                "message": "No se puede realizar la reserva abonada por falta de cupo en alguna de las próximas 4 clases.",
                "clase_id": clase.clase_id,
            }, 409

        if _tiene_reserva_activa(socio_id, clase.clase_id):
            return {
                "status": "already_reserved",
                "message": "Ya tenés una reserva activa en una de las clases del abono.",
                "clase_id": clase.clase_id,
            }, 409

    ahora = _now()
    sancionado = _socio_sancionado_para_descuento(socio_id, ahora)
    descuento_pct = (
        DESCUENTO_ABONO_PCT
        if _en_ventana_descuento(ahora, clase_base.fecha) and not sancionado
        else Decimal("0.00")
    )
    monto_bruto = sum((_decimal_precio_clase(clase) for clase in clases_abono), Decimal("0.00"))
    monto_a_cobrar = _aplicar_descuento(monto_bruto, descuento_pct)
    requiere_pago = monto_a_cobrar > 0

    actividad = _get_or_create_actividad(_clase_actividad_label(clase_base))
    abono = AbonoMensual(
        socio_id=socio_id,
        actividad_id=actividad.actividad_id,
        periodo_inicio=clases_abono[0].fecha,
        periodo_fin=clases_abono[-1].fecha,
        hora_inicio=clase_base.horario_inicio,
        dia_semana=_dia_semana_label(clase_base.fecha),
        descuento_aplicado_pct=descuento_pct,
        prioridad_renovacion=False,
        fecha_limite_renovacion=_fin_mes_siguiente(ahora) if descuento_pct > 0 else None,
        estado="pendiente_pago" if requiere_pago else "activo",
    )
    db.session.add(abono)
    db.session.flush()

    reservas = []
    for clase in clases_abono:
        reserva = Reserva(
            clase_id=clase.clase_id,
            socio_id=socio_id,
            abono_mensual_id=abono.abono_mensual_id,
            tipo_reserva="abonada",
            estado="pendiente_pago" if requiere_pago else "confirmada",
            confirmada_en=None if requiere_pago else ahora,
        )
        db.session.add(reserva)
        reservas.append(reserva)

    try:
        db.session.flush()
    except IntegrityError:
        db.session.rollback()
        return {
            "status": "already_reserved",
            "message": "Ya tenés una reserva activa en una de las clases del abono.",
            "clase_id": clase_base.clase_id,
        }, 409

    if not requiere_pago:
        db.session.commit()
        return {
            "status": "reserved",
            "message": "Reserva abonada confirmada.",
            "abono_mensual_id": abono.abono_mensual_id,
            "reserva_ids": [reserva.reserva_id for reserva in reservas],
            "payment_required": False,
        }, 200

    pago = Pago(
        socio_id=socio_id,
        reserva_id=reservas[0].reserva_id,
        abono_mensual_id=abono.abono_mensual_id,
        proveedor="mercadopago",
        external_ref=str(uuid.uuid4()),
        monto_bruto=monto_bruto,
        descuento_pct=descuento_pct,
        estado="pendiente",
    )
    db.session.add(pago)
    db.session.commit()

    payment_url = _crear_checkout_mercadopago(pago=pago, reserva=reservas[0], clase=clase_base)

    if payment_url is None:
        pago.estado = "error"
        for reserva in reservas:
            reserva.estado = "pago_fallido"
        abono.estado = "pago_fallido"
        db.session.commit()

        return {
            "status": "error",
            "message": "No pudimos iniciar el pago en Mercado Pago. Verificá el MP_ACCESS_TOKEN y la conexión.",
            "abono_mensual_id": abono.abono_mensual_id,
            "pago_id": pago.pago_id,
        }, 502

    message = "Redirigiendo a Mercado Pago para completar el pago."
    if descuento_pct > 0:
        message = "Se aplicó el 20% de descuento. Redirigiendo a Mercado Pago."
    elif sancionado:
        message = "No se aplicó descuento por sanción. Redirigiendo a Mercado Pago."

    return {
        "status": "payment_required",
        "message": message,
        "abono_mensual_id": abono.abono_mensual_id,
        "reserva_id": reservas[0].reserva_id,
        "reserva_ids": [reserva.reserva_id for reserva in reservas],
        "pago_id": pago.pago_id,
        "payment_required": True,
        "payment_url": payment_url,
        "monto_bruto": str(monto_bruto),
        "descuento_pct": str(descuento_pct),
        "monto_a_cobrar": str(monto_a_cobrar),
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


def _get_next_waitlist_entry(clase_id):
    return (
        ListaEspera.query.filter_by(clase_id=clase_id, estado="pendiente")
        .order_by(ListaEspera.posicion.asc(), ListaEspera.creada_en.asc())
        .first()
    )


def _ofrecer_cupo_a_primero(clase):
    if clase is None or _cupo_disponible(clase) <= 0:
        return None

    entry = _get_next_waitlist_entry(clase.clase_id)
    if entry is None:
        return None

    entry.estado = "notificado"
    entry.notificado_en = _now()
    entry.vence_confirmacion_en = _now() + timedelta(minutes=15)
    db.session.flush()

    # Generar token y enviar notificación Telegram
    token = telegram.crear_confirmacion_turno(
        lista_espera_id=entry.lista_espera_id,
        socio_id=entry.socio_id,
        duracion_minutos=15,
    )

    if token:
        clase_data = {
            "actividad": _clase_actividad_label(clase),
            "fecha": clase.fecha.strftime("%Y-%m-%d") if clase.fecha else "",
            "horario_inicio": clase.horario_inicio.strftime("%H:%M") if clase.horario_inicio else "",
            "horario_fin": clase.horario_fin.strftime("%H:%M") if clase.horario_fin else "",
            "cancha": clase.cancha or "",
        }
        # Enviar mensaje (sin romper el flujo si falla)
        telegram.enviar_mensaje_telegram(entry.socio_id, entry.lista_espera_id, clase_data, token)
    else:
        print(f"WARNING: No se pudo generar token para lista_espera_id {entry.lista_espera_id}")

    return entry


def _expire_offers_and_promote():
    ahora = _now()
    expired_entries = (
        ListaEspera.query.filter_by(estado="notificado")
        .filter(ListaEspera.vence_confirmacion_en <= ahora)
        .order_by(ListaEspera.lista_espera_id.asc())
        .all()
    )

    for expired in expired_entries:
        clase = db.session.get(Clase, expired.clase_id)
        expired.estado = "cancelada"
        expired.notificado_en = None
        expired.vence_confirmacion_en = None
        db.session.flush()

        if clase is not None:
            _ofrecer_cupo_a_primero(clase)


def obtener_ofertas_activas():
    socio_id, error = _require_socio()
    if error is not None:
        return error

    _expire_offers_and_promote()

    offers = (
        ListaEspera.query.filter(ListaEspera.socio_id == socio_id)
        .filter(ListaEspera.estado == "notificado")
        .order_by(ListaEspera.notificado_en.asc())
        .all()
    )

    ofertas_data = []
    for offer in offers:
        clase = db.session.get(Clase, offer.clase_id)
        ofertas_data.append(
            {
                "lista_espera_id": offer.lista_espera_id,
                "clase_id": offer.clase_id,
                "actividad": _clase_actividad_label(clase) if clase else None,
                "fecha": clase.fecha.strftime("%Y-%m-%d") if clase else None,
                "horario_inicio": clase.horario_inicio.strftime("%H:%M") if clase else None,
                "horario_fin": clase.horario_fin.strftime("%H:%M") if clase else None,
                "cancha": clase.cancha if clase else None,
                "notificado_en": offer.notificado_en.isoformat() if offer.notificado_en else None,
                "vence_confirmacion_en": offer.vence_confirmacion_en.isoformat() if offer.vence_confirmacion_en else None,
            }
        )

    return {"status": "ok", "ofertas": ofertas_data}, 200


def confirmar_turno(lista_espera_id):
    socio_id, error = _require_socio()
    if error is not None:
        return error

    _expire_offers_and_promote()

    entry = db.session.get(ListaEspera, lista_espera_id)
    if entry is None or entry.socio_id != socio_id:
        return {
            "status": "error",
            "message": "La oferta de turno no existe o no te pertenece.",
        }, 404

    if entry.estado != "notificado":
        return {
            "status": "error",
            "message": "No hay una oferta activa para confirmar.",
        }, 409

    ahora = _now()
    if entry.vence_confirmacion_en is None or entry.vence_confirmacion_en <= ahora:
        entry.estado = "cancelada"
        entry.notificado_en = None
        entry.vence_confirmacion_en = None
        db.session.flush()

        clase = db.session.get(Clase, entry.clase_id)
        if clase is not None:
            _ofrecer_cupo_a_primero(clase)

        return {
            "status": "expired",
            "message": "El tiempo de 15 minutos para confirmar el turno ha expirado, no puede acceder al cupo",
        }, 409

    clase = db.session.get(Clase, entry.clase_id)
    if clase is None:
        return {
            "status": "error",
            "message": "No se encontró la clase asociada a la oferta.",
        }, 404

    if clase.fecha is None or clase.horario_inicio is None:
        return {
            "status": "error",
            "message": "La clase asociada a la oferta tiene datos incompletos.",
        }, 409

    if _schedule_conflict_exists(socio_id, clase):
        return {
            "status": "conflict",
            "message": "No puede confirmar el turno, ya posee una inscripción en ese horario",
        }, 409

    entry.estado = "confirmada"
    entry.confirmada_en = _now()
    entry.vence_confirmacion_en = None
    db.session.commit()

    return {
        "status": "confirmed",
        "message": "Turno asegurado. Completá la reserva en la página de la actividad.",
        "clase_id": clase.clase_id,
        "actividad": _clase_actividad_label(clase),
        "fecha": clase.fecha.strftime("%Y-%m-%d"),
        "horario_inicio": clase.horario_inicio.strftime("%H:%M"),
        "horario_fin": clase.horario_fin.strftime("%H:%M"),
        "cancha": clase.cancha,
    }, 200


def obtener_oferta_desde_token(token):
    """
    Obtiene la información de la oferta asociada a un token.
    
    Returns:
        tuple (oferta_dict, status_code)
    """
    confirmacion, error = telegram.validar_token(token)
    
    if error is not None:
        return error, 400
    
    entry = db.session.get(ListaEspera, confirmacion.lista_espera_id)
    if entry is None:
        return {
            "status": "error",
            "message": "Oferta no encontrada.",
        }, 404
    
    clase = db.session.get(Clase, entry.clase_id)
    if clase is None:
        return {
            "status": "error",
            "message": "La clase asociada no existe.",
        }, 404
    
    return {
        "status": "ok",
        "lista_espera_id": entry.lista_espera_id,
        "clase_id": clase.clase_id,
        "actividad": _clase_actividad_label(clase),
        "fecha": clase.fecha.strftime("%Y-%m-%d") if clase.fecha else "",
        "horario_inicio": clase.horario_inicio.strftime("%H:%M") if clase.horario_inicio else "",
        "horario_fin": clase.horario_fin.strftime("%H:%M") if clase.horario_fin else "",
        "cancha": clase.cancha or "",
        "notificado_en": entry.notificado_en.isoformat() if entry.notificado_en else None,
    }, 200


def confirmar_turno_desde_token(token):
    """
    Confirma un turno desde el link de Telegram (token).
    Similar a confirmar_turno pero sin require_socio, ya que el token identifica al socio.
    
    Returns:
        tuple (response_dict, status_code)
    """
    confirmacion, error = telegram.validar_token(token)
    
    if error is not None:
        return error, 400
    
    socio_id = confirmacion.socio_id
    _expire_offers_and_promote()
    
    entry = db.session.get(ListaEspera, confirmacion.lista_espera_id)
    if entry is None:
        return {
            "status": "error",
            "message": "La oferta no existe.",
        }, 404
    
    if entry.estado != "notificado":
        return {
            "status": "error",
            "message": "La oferta ya no es válida.",
        }, 409
    
    clase = db.session.get(Clase, entry.clase_id)
    if clase is None:
        return {
            "status": "error",
            "message": "La clase no existe.",
        }, 404
    
    if clase.fecha is None or clase.horario_inicio is None:
        return {
            "status": "error",
            "message": "La clase tiene datos incompletos.",
        }, 409
    
    if _schedule_conflict_exists(socio_id, clase):
        return {
            "status": "conflict",
            "message": "No puede confirmar el turno, ya posee una inscripción en ese horario",
        }, 409
    
    # Marcar confirmación y entrada de lista_espera como confirmada
    entry.estado = "confirmada"
    entry.confirmada_en = _now()
    entry.vence_confirmacion_en = None
    
    telegram.marcar_confirmacion_como_confirmada(token)
    
    db.session.commit()
    
    return {
        "status": "confirmed",
        "message": "Turno asegurado. Completá la reserva en la página de la actividad.",
        "clase_id": clase.clase_id,
        "actividad": _clase_actividad_label(clase),
        "fecha": clase.fecha.strftime("%Y-%m-%d"),
        "horario_inicio": clase.horario_inicio.strftime("%H:%M"),
        "horario_fin": clase.horario_fin.strftime("%H:%M"),
        "cancha": clase.cancha,
    }, 200


def abandonar_lista_espera(lista_espera_id):
    socio_id, error = _require_socio()
    if error is not None:
        return error

    entry = db.session.get(ListaEspera, lista_espera_id)
    if entry is None or entry.socio_id != socio_id:
        return {
            "status": "error",
            "message": "La entrada de lista de espera no existe o no te pertenece.",
        }, 404

    if entry.estado == "cancelada":
        return {
            "status": "ok",
            "message": "La entrada ya fue cancelada.",
        }, 200

    clase = db.session.get(Clase, entry.clase_id)

    # Guardar posicion para recolocar a los demas
    posicion = entry.posicion

    entry.estado = "cancelada"
    entry.notificado_en = None
    entry.vence_confirmacion_en = None
    entry.confirmada_en = None
    db.session.flush()

    # Reajustar posiciones de los que estaban por detras
    db.session.execute(
        ListaEspera.__table__.update()
        .where(ListaEspera.clase_id == entry.clase_id)
        .where(ListaEspera.posicion > posicion)
        .values({"posicion": ListaEspera.posicion - 1})
    )

    # Si estaba notificado, ofrecer el cupo al siguiente
    if clase is not None:
        _ofrecer_cupo_a_primero(clase)

    db.session.commit()

    return {"status": "ok", "message": "Se abandono la lista de espera existosamente."}, 200


def _schedule_conflict_exists(socio_id, clase):
    return (
        Reserva.query.join(Clase)
        .filter(Reserva.socio_id == socio_id)
        .filter(Reserva.estado.in_(sorted(RESERVA_ESTADOS_OCUPAN_CUPO)))
        .filter(Clase.fecha == clase.fecha)
        .filter(Clase.horario_inicio == clase.horario_inicio)
        .first()
        is not None
    )


def _build_espontanea_reserva(clase, socio_id):
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
    db.session.flush()
    return reserva, credito, requiere_pago, precio


def procesar_retorno_pago(reserva_id, pago_status, payment_id=None, external_reference=None):
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

    normalized = _estado_pago_retorno(
        pago,
        pago_status,
        payment_id=payment_id,
        external_reference=external_reference,
    )

    if reserva.estado == "confirmada":
        return {
            "status": "reserved",
            "message": "La reserva ya estaba confirmada.",
            "reserva_id": reserva.reserva_id,
        }, 200

    if normalized in {"approved", "aprobado", "success", "accredited"}:
        ahora = _now()
        reservas_a_confirmar = _reservas_del_mismo_abono(reserva)
        for reserva_abono in reservas_a_confirmar:
            reserva_abono.estado = "confirmada"
            reserva_abono.confirmada_en = ahora

        if reserva.abono_mensual_id is not None:
            abono = db.session.get(AbonoMensual, reserva.abono_mensual_id)
            if abono is not None:
                abono.estado = "activo"

        pago.estado = "aprobado"
        pago.fecha_pago = ahora
        pago.monto_pagado = _importe_a_cobrar(pago)

        db.session.commit()

        if reserva.abono_mensual_id is not None:
            return {
                "status": "reserved",
                "message": "Reserva abonada confirmada.",
                "reserva_id": reserva.reserva_id,
                "abono_mensual_id": reserva.abono_mensual_id,
            }, 200

        return {
            "status": "reserved",
            "message": "Reserva confirmada.",
            "reserva_id": reserva.reserva_id,
        }, 200

    if normalized in {"pending", "in_process", "in_mediation"}:
        pago.estado = "pendiente"
        db.session.commit()
        return {
            "status": "payment_pending",
            "message": "El pago quedó pendiente. Cuando se acredite, se confirmará la inscripción.",
            "reserva_id": reserva.reserva_id,
        }, 200

    reservas_a_rechazar = _reservas_del_mismo_abono(reserva)
    for reserva_abono in reservas_a_rechazar:
        reserva_abono.estado = "pago_fallido"

    if reserva.abono_mensual_id is not None:
        abono = db.session.get(AbonoMensual, reserva.abono_mensual_id)
        if abono is not None:
            abono.estado = "pago_fallido"

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
    
    lista_espera_data = _listar_lista_espera_socio(socio_id)

    reservas = (
        Reserva.query.options(joinedload(Reserva.clase))
        .filter(Reserva.socio_id == socio_id)
        .filter(Reserva.estado.in_(sorted(RESERVA_ESTADOS_OCUPAN_CUPO)))
        .order_by(Reserva.creada_en.desc())
        .all()
    )

    if not reservas:
        return {"status": "ok", "reservas": [], "lista_espera":lista_espera_data}, 200

    reserva_ids = [reserva.reserva_id for reserva in reservas]
    abono_ids = [
        reserva.abono_mensual_id
        for reserva in reservas
        if reserva.abono_mensual_id is not None
    ]
    pagos = (
        Pago.query.filter(
            db.or_(
                Pago.reserva_id.in_(reserva_ids),
                Pago.abono_mensual_id.in_(abono_ids) if abono_ids else db.false(),
            )
        )
        .order_by(Pago.pago_id.desc())
        .all()
    )
    pagos_por_reserva = {}
    pagos_por_abono = {}
    for pago in pagos:
        if pago.reserva_id not in pagos_por_reserva:
            pagos_por_reserva[pago.reserva_id] = pago
        if pago.abono_mensual_id is not None and pago.abono_mensual_id not in pagos_por_abono:
            pagos_por_abono[pago.abono_mensual_id] = pago

    cantidad_reservas_por_abono = {}
    if abono_ids:
        cantidades = (
            db.session.query(Reserva.abono_mensual_id, db.func.count(Reserva.reserva_id))
            .filter(Reserva.abono_mensual_id.in_(abono_ids))
            .group_by(Reserva.abono_mensual_id)
            .all()
        )
        cantidad_reservas_por_abono = {
            abono_id: int(cantidad)
            for abono_id, cantidad in cantidades
        }

    ahora = _now()
    reservas_data = []
    for reserva in reservas:
        clase = reserva.clase
        clase_inicio = _clase_inicio(clase)
        puede_cancelar = _puede_cancelar_reserva(reserva, clase_inicio, ahora)
        pago = pagos_por_reserva.get(reserva.reserva_id)
        if pago is None and reserva.abono_mensual_id is not None:
            pago = pagos_por_abono.get(reserva.abono_mensual_id)

        # print("puede cancelar "+ str(puede_cancelar))

        if pago and pago.estado == "pendiente":
            puede_cancelar = False
            print("ASDFSDFASDFASDFASDFASDFASDFASDFASDFASDFASD: ", reserva.reserva_id, pago.pago_id, pago.estado)

        # print("puede cancelar "+ str(puede_cancelar))

        reintegro_estimado = _calcular_reintegro_estimado_reserva(reserva, pago, clase_inicio, ahora)
        reintegro_aplica = reintegro_estimado is not None
        monto_pagado_reserva = _monto_pagado_para_reserva(
            pago,
            reserva,
            cantidad_reservas_por_abono,
        )

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
                "monto_pagado": str(monto_pagado_reserva) if monto_pagado_reserva is not None else None,
                "puede_cancelar": puede_cancelar,
                "reintegro_aplica": reintegro_aplica,
                "reintegro_estimado": str(reintegro_estimado) if reintegro_estimado is not None else None,
            }
        )

    
    abonos_body, abonos_status = listar_abonos_mensuales_socio()
    if abonos_status != 200:
        return abonos_body, abonos_status

    return {
        "status": "ok",
        "reservas": reservas_data,
        "lista_espera": lista_espera_data,
        "abonos": abonos_body.get("abonos", []),
    }, 200


def listar_abonos_mensuales_socio():
    socio_id, error = _require_socio()
    if error is not None:
        return error

    abonos = (
        AbonoMensual.query.filter_by(socio_id=socio_id)
        .order_by(AbonoMensual.periodo_inicio.desc())
        .all()
    )

    hoy = date.today()
    abonos_data = []
    for abono in abonos:
        actividad = db.session.get(Actividad, abono.actividad_id)
        fecha_limite = abono.fecha_limite_renovacion
        renovable = (
            abono.estado == "activo"
            and 1 <= hoy.day <= 10
            and (fecha_limite is None or hoy <= fecha_limite)
        )

        abonos_data.append(
            {
                "abono_mensual_id": abono.abono_mensual_id,
                "actividad": actividad.nombre if actividad else None,
                "periodo_inicio": abono.periodo_inicio.isoformat() if abono.periodo_inicio else None,
                "periodo_fin": abono.periodo_fin.isoformat() if abono.periodo_fin else None,
                "hora_inicio": abono.hora_inicio.strftime("%H:%M") if abono.hora_inicio else None,
                "dia_semana": abono.dia_semana,
                "fecha_limite_renovacion": fecha_limite.isoformat() if fecha_limite else None,
                "estado": abono.estado,
                "renovable": renovable,
                "cancelable": abono.estado == "activo",
            }
        )

    return {"status": "ok", "abonos": abonos_data}, 200


def cancelar_abono_mensual(abono_id):
    socio_id, error = _require_socio()
    if error is not None:
        return error

    abono = db.session.get(AbonoMensual, abono_id)
    if abono is None or abono.socio_id != socio_id:
        return {
            "status": "error",
            "message": "El abono mensual no existe o no te pertenece.",
        }, 404

    if abono.estado != "activo":
        return {
            "status": "error",
            "message": "El abono mensual no está activo.",
        }, 409

    abono.estado = "cancelado"
    db.session.commit()

    return {
        "status": "ok",
        "message": "Abono mensual cancelado.",
        "abono_mensual_id": abono.abono_mensual_id,
    }, 200


def renovar_abono_mensual(abono_id):
    socio_id, error = _require_socio()
    if error is not None:
        return error

    abono = db.session.get(AbonoMensual, abono_id)
    if abono is None or abono.socio_id != socio_id:
        return {
            "status": "error",
            "message": "El abono mensual no existe o no te pertenece.",
        }, 404

    if abono.estado != "activo":
        return {
            "status": "error",
            "message": "Solo se pueden renovar abonos activos.",
        }, 409

    hoy = date.today()
    if not (1 <= hoy.day <= 10):
        return {
            "status": "error",
            "message": "Solo se puede renovar entre el 1 y 10 del mes.",
        }, 409

    if abono.fecha_limite_renovacion is not None and hoy > abono.fecha_limite_renovacion:
        return {
            "status": "error",
            "message": "La fecha límite de renovación ya pasó.",
        }, 409

    siguiente_inicio = abono.periodo_fin + timedelta(days=1)
    siguiente_ultimo_dia = calendar.monthrange(siguiente_inicio.year, siguiente_inicio.month)[1]
    siguiente_fin = date(siguiente_inicio.year, siguiente_inicio.month, siguiente_ultimo_dia)
    abono.periodo_inicio = siguiente_inicio
    abono.periodo_fin = siguiente_fin
    abono.fecha_limite_renovacion = date(
        siguiente_inicio.year,
        siguiente_inicio.month,
        min(10, siguiente_ultimo_dia),
    )

    db.session.commit()

    return {
        "status": "ok",
        "message": "Abono mensual renovado.",
        "abono_mensual_id": abono.abono_mensual_id,
        "periodo_inicio": abono.periodo_inicio.isoformat(),
        "periodo_fin": abono.periodo_fin.isoformat(),
        "fecha_limite_renovacion": abono.fecha_limite_renovacion.isoformat(),
    }, 200


def _monto_pagado_para_reserva(pago, reserva, cantidad_reservas_por_abono):
    if pago is None or pago.monto_pagado is None:
        return None

    monto_pagado = Decimal(str(pago.monto_pagado))
    if reserva.abono_mensual_id is None:
        return monto_pagado

    cantidad_reservas = cantidad_reservas_por_abono.get(reserva.abono_mensual_id, CLASES_POR_ABONO)
    if cantidad_reservas <= 0:
        cantidad_reservas = CLASES_POR_ABONO

    return (monto_pagado / Decimal(cantidad_reservas)).quantize(Decimal("0.01"))


def _calcular_reintegro_estimado_reserva(reserva, pago, clase_inicio, ahora):
    if reserva.tipo_reserva == "abonada":
        if clase_inicio is not None and clase_inicio - ahora > timedelta(hours=24):
            return "1 credito"

        return None

    return _calcular_reintegro_estimada(pago, clase_inicio, ahora)


def _listar_lista_espera_socio(socio_id):
    entries = (
        ListaEspera.query.filter(ListaEspera.socio_id == socio_id)
        .filter(ListaEspera.estado.in_(["pendiente", "notificado"]))
        .order_by(ListaEspera.creada_en.desc())
        .all()
    )

    lista_espera_data = []
    for entry in entries:
        clase = db.session.get(Clase, entry.clase_id)
        lista_espera_data.append(
            {
                "lista_espera_id": entry.lista_espera_id,
                "clase_id": entry.clase_id,
                "actividad": _clase_actividad_label(clase) if clase else None,
                "fecha": clase.fecha.strftime("%Y-%m-%d") if clase else None,
                "horario_inicio": clase.horario_inicio.strftime("%H:%M") if clase else None,
                "horario_fin": clase.horario_fin.strftime("%H:%M") if clase else None,
                "cancha": clase.cancha if clase else None,
                "estado": entry.estado,
                "posicion": entry.posicion,
                "notificado_en": entry.notificado_en.isoformat() if entry.notificado_en else None,
                "vence_confirmacion_en": entry.vence_confirmacion_en.isoformat() if entry.vence_confirmacion_en else None,
            }
        )

    return lista_espera_data


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

    if clase is not None:
        _ofrecer_cupo_a_primero(clase)

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
        scenario_message = "Se reembolso el 50% del valor de la clase."
    elif not reintegro_aplica and not sancion_aplicada:
        scenario_code = "escenario_2"
        scenario_message = ""
    elif reintegro_aplica and sancion_aplicada:
        scenario_code = "escenario_3"
        scenario_message =  "Se reembolso el 50% del valor de la clase. Se aplico una sancion por cancelar 3 o más clases en el mes"
    else:
        scenario_code = "escenario_4"
        scenario_message = "Se aplico una sancion por cancelar 3 o más clases en el mes"

    return {
        "status": "cancelled",
        "message": "Cancelacion correcta.",
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


def cancelar_reserva_abonada(reserva_id, confirmar_sancion=False):
    socio_id, error = _require_socio()
    if error is not None:
        return error

    reserva = db.session.get(Reserva, reserva_id)
    if reserva is None or reserva.socio_id != socio_id:
        return {
            "status": "error",
            "message": "La reserva indicada no existe o no te pertenece.",
        }, 404

    if reserva.tipo_reserva != "abonada" or reserva.abono_mensual_id is None:
        return {
            "status": "error",
            "message": "Solo se pueden cancelar reservas abonadas.",
        }, 409

    if reserva.estado != "confirmada":
        return {
            "status": "error",
            "message": "Solo se pueden cancelar reservas abonadas confirmadas.",
        }, 409

    abono = db.session.get(AbonoMensual, reserva.abono_mensual_id)
    if abono is None or abono.estado != "activo":
        return {
            "status": "error",
            "message": "No se encontro un abono mensual activo para la reserva.",
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

    cancelaciones_previas_mes = _contar_cancelaciones_mes(socio_id, ahora)
    sancion_aplicaria = cancelaciones_previas_mes + 1 >= 3
    if sancion_aplicaria and not confirmar_sancion:
        return {
            "status": "requires_sanction_confirmation",
            "message": "Esta cancelacion aplica una sancion: perderas el beneficio del 20% de descuento para el abono del mes siguiente.",
            "reserva_id": reserva.reserva_id,
            "cancelaciones_mes": cancelaciones_previas_mes,
        }, 409

    credito_info = {
        "aplica": False,
        "credito_id": None,
        "message": "No se otorga credito porque faltan menos de 24 horas para el inicio de la clase.",
    }
    if clase_inicio - ahora > timedelta(hours=24):
        credito = Credito(
            socio_id=socio_id,
            cancelacion_reserva_origen_id=reserva.reserva_id,
            clase_cancelada_origen_id=reserva.clase_id,
            otorgado_en=ahora,
            estado="disponible",
        )
        db.session.add(credito)
        db.session.flush()
        credito_info = {
            "aplica": True,
            "credito_id": credito.credito_id,
            "message": "Se otorgo un credito equivalente a una clase.",
        }

    reserva.estado = "cancelada"
    reserva.cancelada_en = ahora
    db.session.flush()

    if clase is not None:
        _ofrecer_cupo_a_primero(clase)

    cancelaciones_mes = _contar_cancelaciones_mes(socio_id, ahora)
    sancion_aplicada = cancelaciones_mes >= 3
    descuento_bloqueado_hasta = None
    if sancion_aplicada:
        socio = db.session.get(Socio, socio_id)
        if socio is not None:
            descuento_bloqueado_hasta = _fin_mes_siguiente(ahora)
            socio.descuento_bloqueado_hasta = descuento_bloqueado_hasta

    db.session.commit()

    if credito_info["aplica"] and not sancion_aplicada:
        scenario_code = "escenario_1"
        scenario_message = "Se otorgo un credito equivalente a una clase."
    elif not credito_info["aplica"] and not sancion_aplicada:
        scenario_code = "escenario_2"
        scenario_message = "No recibiras reintegro ni credito por cancelar con menos de 24 horas de anticipacion."
    elif credito_info["aplica"] and sancion_aplicada:
        scenario_code = "escenario_3"
        scenario_message = "Se otorgo un credito equivalente a una clase. Se aplico una sancion por cancelar 3 o mas clases en el mes."
    else:
        scenario_code = "escenario_4"
        scenario_message = "No recibiras reintegro ni credito por cancelar con menos de 24 horas de anticipacion. Se aplico una sancion por cancelar 3 o mas clases en el mes."

    return {
        "status": "cancelled",
        "message": "Cancelacion de reserva abonada correcta.",
        "scenario": scenario_code,
        "scenario_message": scenario_message,
        "reserva_id": reserva.reserva_id,
        "credito": credito_info,
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
                "title": _titulo_pago(pago, clase),
                "quantity": 1,
                "currency_id": "ARS",
                "unit_price": float(_importe_a_cobrar(pago)),
            }
        ],
        "external_reference": pago.external_ref,
        "back_urls": return_urls,
    }

    if frontend_base.startswith("https://"):
        preference_payload["auto_return"] = "approved"

    try:
        print(
            "Mercado Pago preference payload:",
            json.dumps(preference_payload, ensure_ascii=False),
        )

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

        print(
            "Mercado Pago preference response:",
            json.dumps(
                {
                    "id": preference.get("id"),
                    "init_point": preference.get("init_point"),
                    "sandbox_init_point": preference.get("sandbox_init_point"),
                    "external_reference": preference.get("external_reference"),
                    "auto_return": preference.get("auto_return"),
                    "back_urls": preference.get("back_urls"),
                    "items": preference.get("items"),
                },
                ensure_ascii=False,
            ),
        )

        init_point = _checkout_url_from_preference(preference, access_token)
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


def _checkout_url_from_preference(preference, access_token):
    if not preference:
        return None

    is_test_token = str(access_token or "").upper().startswith("TEST-")
    if is_test_token:
        return preference.get("sandbox_init_point") or preference.get("init_point")

    return preference.get("init_point") or preference.get("sandbox_init_point")


def _puede_cancelar_reserva(reserva, clase_inicio, ahora):
    if reserva is None or clase_inicio is None:
        print("1")
        return False


    if reserva.estado not in RESERVA_ESTADOS_OCUPAN_CUPO:
        print("2")
        return False

    # print("clase_inicio > ahora: "+ str(clase_inicio > ahora))
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


def _estado_pago_retorno(pago, pago_status, payment_id=None, external_reference=None):
    if payment_id or external_reference:
        estado_mp = _consultar_estado_pago_mp(
            payment_id=payment_id,
            external_reference=external_reference or pago.external_ref,
        )
        if estado_mp:
            return estado_mp

    return (pago_status or "").strip().lower()


def _consultar_estado_pago_mp(payment_id=None, external_reference=None):
    access_token = (os.environ.get("MP_ACCESS_TOKEN") or "").strip()
    if not access_token:
        return None

    if payment_id:
        status = _consultar_estado_pago_mp_por_id(payment_id, access_token)
        if status:
            return status

    payment_id_from_ref = _buscar_pago_mp_id(external_reference, access_token)
    if payment_id_from_ref:
        return _consultar_estado_pago_mp_por_id(payment_id_from_ref, access_token)

    return None


def _consultar_estado_pago_mp_por_id(payment_id, access_token):
    try:
        request = Request(
            f"https://api.mercadopago.com/v1/payments/{payment_id}",
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
        print("Mercado Pago payment lookup failed:", exc.code, body)
        return None
    except (URLError, ValueError, OSError) as exc:
        print("Mercado Pago payment lookup failed:", str(exc))
        return None

    return (payload.get("status") or payload.get("status_detail") or "").strip().lower()


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


def _buscar_clases_consecutivas(clase_base):
    clases = []
    for offset in range(CLASES_POR_ABONO):
        clase = (
            Clase.query.filter(Clase.actividad == clase_base.actividad)
            .filter(Clase.fecha == clase_base.fecha + timedelta(days=7 * offset))
            .filter(Clase.horario_inicio == clase_base.horario_inicio)
            .order_by(Clase.clase_id.asc())
            .first()
        )
        if clase is None:
            return []
        clases.append(clase)

    return clases


def _tiene_reserva_activa(socio_id, clase_id):
    return (
        Reserva.query.filter_by(clase_id=clase_id, socio_id=socio_id)
        .filter(Reserva.estado.in_(sorted(RESERVA_ESTADOS_OCUPAN_CUPO)))
        .first()
        is not None
    )


def _decimal_precio_clase(clase):
    precio = getattr(clase, "precio", None)
    if precio is None:
        return Decimal("0.00")

    return Decimal(str(precio)).quantize(Decimal("0.01"))


def _en_ventana_descuento(ahora, fecha_clase):
    fecha_limite = date(fecha_clase.year, fecha_clase.month, 10)
    return ahora.date() <= fecha_limite


def _socio_sancionado_para_descuento(socio_id, ahora):
    socio = db.session.get(Socio, socio_id)
    if socio is None or socio.descuento_bloqueado_hasta is None:
        return False

    return socio.descuento_bloqueado_hasta >= ahora.date()


def _aplicar_descuento(monto, descuento_pct):
    descuento = Decimal(str(descuento_pct or 0))
    multiplier = Decimal("1.00") - (descuento / Decimal("100.00"))
    return (Decimal(str(monto)) * multiplier).quantize(Decimal("0.01"))


def _importe_a_cobrar(pago):
    return _aplicar_descuento(_monto_base_pago(pago), getattr(pago, "descuento_pct", 0))


def _get_or_create_actividad(nombre):
    actividad = Actividad.query.filter_by(nombre=nombre).first()
    if actividad is not None:
        return actividad

    actividad = Actividad(nombre=nombre)
    db.session.add(actividad)
    db.session.flush()
    return actividad


def _dia_semana_label(fecha):
    dias = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    return dias[fecha.weekday()]


def _reservas_del_mismo_abono(reserva):
    if reserva.abono_mensual_id is None:
        return [reserva]

    return (
        Reserva.query.filter_by(abono_mensual_id=reserva.abono_mensual_id)
        .order_by(Reserva.reserva_id.asc())
        .all()
    )


def _titulo_pago(pago, clase):
    if getattr(pago, "abono_mensual_id", None) is not None:
        return f"Reserva abonada {_clase_actividad_label(clase)} x4"

    return f"Clase {_clase_actividad_label(clase)}"
