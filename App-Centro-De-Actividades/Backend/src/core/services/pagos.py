from datetime import datetime, timedelta

from flask_login import current_user

from src.core.models.pago import Pago


def listar_pagos_socio(filters=None):
    if not current_user.is_authenticated:
        return {
            "status": "error",
            "message": "Debes iniciar sesión para ver tus pagos.",
        }, 401

    if current_user.role != "socio":
        return {
            "status": "error",
            "message": "Solo los socios pueden ver sus pagos.",
        }, 403

    filters = filters or {}
    start_date, end_date, errors = _parse_filters(filters)
    if errors:
        return {"status": "validation_error", "errors": errors}, 400

    query = Pago.query.filter_by(socio_id=current_user.persona_id)

    # filtro la query, en caso de que sea pendiente, no lo muestro
    query = query.filter(Pago.estado == "aprobado")

    if start_date is not None:
        query = query.filter(Pago.fecha_pago >= start_date)

    if end_date is not None:
        query = query.filter(Pago.fecha_pago <= end_date)

    pagos = query.order_by(Pago.fecha_pago.desc().nullslast(), Pago.pago_id.desc()).all()

    return {
        "status": "ok",
        "payments": [_serializar_pago(pago) for pago in pagos],
        "filters": {
            "start_date": filters.get("start_date") or "",
            "end_date": filters.get("end_date") or "",
        },
    }, 200


def _parse_filters(filters):
    errors = {}
    start_date = _parse_date(filters.get("start_date"))
    end_date = _parse_date(filters.get("end_date"), end_of_day=True)

    today = datetime.utcnow().date()

    if filters.get("start_date") and start_date is None:
        errors["start_date"] = "Fecha de inicio inválida. Usa el formato YYYY-MM-DD."
    elif start_date is not None and start_date.date() > today:
        errors["start_date"] = "La fecha desde no puede ser mayor a hoy."

    if filters.get("end_date") and end_date is None:
        errors["end_date"] = "Fecha de fin inválida. Usa el formato YYYY-MM-DD."
    elif end_date is not None and end_date.date() > today:
        errors["end_date"] = "La fecha hasta no puede ser mayor a hoy."

    return start_date, end_date, errors


def _parse_date(value, end_of_day=False):
    if value is None:
        return None

    normalized = str(value).strip()
    if not normalized:
        return None

    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        try:
            parsed = datetime.fromisoformat(f"{normalized}T00:00:00")
        except ValueError:
            return None

    if end_of_day:
        if parsed.hour == 0 and parsed.minute == 0 and parsed.second == 0 and parsed.microsecond == 0:
            parsed = parsed + timedelta(days=1) - timedelta(microseconds=1)

    return parsed


def _serializar_pago(pago):
    return {
        "pago_id": pago.pago_id,
        "reserva_id": pago.reserva_id,
        "abono_mensual_id": pago.abono_mensual_id,
        "proveedor": pago.proveedor,
        "external_ref": pago.external_ref,
        "monto_bruto": str(pago.monto_bruto),
        "descuento_pct": str(pago.descuento_pct),
        "monto_pagado": str(pago.monto_pagado) if pago.monto_pagado is not None else None,
        "estado": pago.estado,
        "fecha_pago": pago.fecha_pago.isoformat() if pago.fecha_pago is not None else None,
    }
