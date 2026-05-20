from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload
from src.core.database import db
from src.core.models.persona import Persona
from flask_login import current_user

from src.core.models.pago import Pago
from src.core.models.persona import Socio


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

def _normalizar_filtros_pagos(filters):
    filters = filters or {}
    return {
        "dni": (filters.get("dni") or "").strip(),
        "email": (filters.get("email") or "").strip().lower(),
        "nombre": (filters.get("nombre") or "").strip().lower(),
        "fecha_desde": filters.get("fecha_desde"),
        "fecha_hasta": filters.get("fecha_hasta"),
    }

def listar_pagos(filters=None):
    normalized_filters = _normalizar_filtros_pagos(filters)

    query = Pago.query.options(
        joinedload(Pago.socio).joinedload(Socio.persona).joinedload(Persona.persona_roles)
    )

    # Filtro por DNI
    if normalized_filters["dni"]:
        query = query.join(Pago.socio).join(Socio.persona).filter(Persona.dni == normalized_filters["dni"])

    # Filtro por email
    if normalized_filters["email"]:
        query = query.join(Pago.socio).join(Socio.persona).filter(
            db.func.lower(Persona.email) == normalized_filters["email"]
        )

    # Filtro por nombre completo
    if normalized_filters["nombre"]:
        nombre_completo = db.func.lower(Persona.nombre + " " + Persona.apellido)
        query = query.join(Pago.socio).join(Socio.persona).filter(
            nombre_completo.contains(normalized_filters["nombre"])
        )

    # Filtro por rango de fechas
    if normalized_filters["fecha_desde"] and normalized_filters["fecha_hasta"]:
        fecha_desde = datetime.strptime(normalized_filters["fecha_desde"], "%d/%m/%Y")
        fecha_hasta = datetime.strptime(normalized_filters["fecha_hasta"], "%d/%m/%Y")

        if fecha_desde > fecha_hasta:
            return {
                "status": "error",
                "message": "La fecha desde no puede ser mayor a la fecha hasta",
                "filters": normalized_filters,
            }, 400

        query = query.filter(Pago.fecha_pago >= fecha_desde, Pago.fecha_pago <= fecha_hasta)

    pagos = query.order_by(Pago.fecha_pago.desc()).all()

    return {
        "status": "ok",
        "filters": normalized_filters,
        "pagos": [_serializar_pago(p) for p in pagos],
    }, 200


def _serializar_pago(pago: Pago):
    return {
        "pago_id": pago.pago_id,
        "socio_id": pago.socio_id,
        "dni": pago.socio.persona.dni if pago.socio and pago.socio.persona else None,
        "email": pago.socio.persona.email if pago.socio and pago.socio.persona else None,
        "nombre_completo": pago.socio.persona.nombre_completo if pago.socio and pago.socio.persona else None,
        "reserva_id": pago.reserva_id,
        "abono_mensual_id": pago.abono_mensual_id,
        "proveedor": pago.proveedor,
        "external_ref": pago.external_ref,
        "monto_bruto": str(pago.monto_bruto),
        "descuento_pct": str(pago.descuento_pct),
        "monto_pagado": str(pago.monto_pagado) if pago.monto_pagado else None,
        "estado": pago.estado,
        "fecha_pago": pago.fecha_pago.isoformat() if pago.fecha_pago else None,
    }
