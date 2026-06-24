from datetime import datetime
from decimal import Decimal

from src.core.database import db
from src.core.enums.clase_enum import ActividadEnum
from src.core.models.abono_mensual import AbonoMensual
from src.core.models.actividad import Actividad
from src.core.models.clase import Clase
from src.core.models.pago import Pago
from src.core.models.persona import Persona, Socio
from src.core.models.reserva import Reserva
from src.core.seeds.clases import (
    _build_abono_mensual_clases_to_seed,
    get_seed_reference_datetime,
)


def seed_abonos_mensuales(seed_datetime=None):
    seed_datetime = get_seed_reference_datetime(seed_datetime)

    clases_abono = _get_clases_abono(seed_datetime)
    if len(clases_abono) != 4:
        print("[SEED] No se crearon abonos mensuales: faltan clases consecutivas de abono.")
        return

    periodo_inicio = clases_abono[0].fecha
    periodo_fin = clases_abono[-1].fecha
    hora_inicio = clases_abono[0].horario_inicio
    fecha_limite_renovacion = _fecha_limite_renovacion_siguiente(periodo_inicio)
    dia_semana = _dia_semana_label(periodo_inicio)

    socios = _get_socios_para_abonos()
    actividad = Actividad.query.filter_by(nombre="Futbol").first()

    if not socios or actividad is None:
        print("[SEED] No hay socios o actividad Futbol para seedear abonos mensuales.")
        return

    created = 0
    updated = 0

    for socio in socios:
        socio_id = getattr(socio, "persona_id", None)

        abono = (
            AbonoMensual.query.filter_by(
                socio_id=socio_id,
                actividad_id=actividad.actividad_id,
            )
            .filter(AbonoMensual.periodo_inicio == periodo_inicio)
            .first()
        )

        if abono is None:
            abono = AbonoMensual(
                socio_id=socio_id,
                actividad_id=actividad.actividad_id,
                periodo_inicio=periodo_inicio,
                periodo_fin=periodo_fin,
                hora_inicio=hora_inicio,
                dia_semana=dia_semana,
                descuento_aplicado_pct=20,
                prioridad_renovacion=False,
                fecha_limite_renovacion=fecha_limite_renovacion,
                estado="activo",
            )
            db.session.add(abono)
            created += 1
        else:
            abono.periodo_fin = periodo_fin
            abono.hora_inicio = hora_inicio
            abono.dia_semana = dia_semana
            abono.fecha_limite_renovacion = fecha_limite_renovacion
            abono.estado = "activo"
            updated += 1

        db.session.flush()

        for clase in clases_abono:
            reserva = Reserva.query.filter_by(
                clase_id=clase.clase_id,
                socio_id=socio_id,
            ).first()

            if reserva is None:
                reserva = Reserva(
                    clase_id=clase.clase_id,
                    socio_id=socio_id,
                    abono_mensual_id=abono.abono_mensual_id,
                    tipo_reserva="abonada",
                    estado="confirmada",
                    creada_en=seed_datetime,
                    confirmada_en=seed_datetime,
                )
                db.session.add(reserva)
            else:
                reserva.abono_mensual_id = abono.abono_mensual_id
                reserva.tipo_reserva = "abonada"
                reserva.estado = "confirmada"
                reserva.confirmada_en = reserva.confirmada_en or seed_datetime

        _ensure_pago_abono(socio_id, abono, clases_abono, seed_datetime)

    db.session.commit()
    print(f"[SEED] Seeded {created} abonos mensuales; actualizados {updated}.")


def _get_clases_abono(seed_datetime):
    clases = []
    for clase_data in _build_abono_mensual_clases_to_seed(seed_datetime):
        fecha = datetime.strptime(clase_data["fecha"], "%Y-%m-%d").date()
        horario_inicio = datetime.strptime(clase_data["horario_inicio"], "%H:%M").time()
        clase = Clase.query.filter_by(
            actividad=ActividadEnum(clase_data["actividad"]),
            fecha=fecha,
            horario_inicio=horario_inicio,
        ).first()
        if clase is not None:
            clases.append(clase)

    return clases


def _get_socios_para_abonos():
    socios = []
    socio_centro = (
        Socio.query.join(Persona, Persona.persona_id == Socio.persona_id)
        .filter(Persona.email == "socio@centro.test")
        .first()
    )
    if socio_centro is not None:
        socios.append(socio_centro)

    for socio in Socio.query.order_by(Socio.persona_id.asc()).limit(5).all():
        if all(existing.persona_id != socio.persona_id for existing in socios):
            socios.append(socio)

    return socios[:5]


def _ensure_pago_abono(socio_id, abono, clases_abono, seed_datetime):
    external_ref = f"seed-abono-{abono.abono_mensual_id}"
    monto_bruto = sum((_decimal_precio_clase(clase) for clase in clases_abono), Decimal("0.00"))
    descuento_pct = Decimal(str(abono.descuento_aplicado_pct or 0))
    monto_pagado = (
        monto_bruto * (Decimal("100.00") - descuento_pct) / Decimal("100.00")
    ).quantize(Decimal("0.01"))

    pago = Pago.query.filter_by(external_ref=external_ref).first()
    if pago is None:
        pago = Pago(
            socio_id=socio_id,
            reserva_id=None,
            abono_mensual_id=abono.abono_mensual_id,
            proveedor="mercadopago",
            external_ref=external_ref,
        )
        db.session.add(pago)

    pago.monto_bruto = monto_bruto
    pago.descuento_pct = descuento_pct
    pago.monto_pagado = monto_pagado
    pago.estado = "aprobado"
    pago.fecha_pago = seed_datetime


def _decimal_precio_clase(clase):
    if clase.precio is None:
        return Decimal("0.00")

    return Decimal(str(clase.precio)).quantize(Decimal("0.01"))


def _fecha_limite_renovacion_siguiente(fecha_periodo):
    year = fecha_periodo.year + (1 if fecha_periodo.month == 12 else 0)
    month = 1 if fecha_periodo.month == 12 else fecha_periodo.month + 1
    return fecha_periodo.replace(year=year, month=month, day=10)


def _dia_semana_label(fecha):
    dias = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
    return dias[fecha.weekday()]
