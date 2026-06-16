import pandas as pd
from decimal import Decimal
from datetime import datetime, date, timezone
import calendar
from sqlalchemy import func, or_
from src.core.database import db
from src.core.models import Pago, Asistencia, Reserva, Clase,  ListaEspera


def obtener_dashboard_metricas(anio=None, mes=None):

    anio = int(anio) if anio else datetime.now().year
    
    if mes and mes.isdigit() and 1 <= int(mes) <= 12:
        mes = int(mes)
        ultimo_dia = calendar.monthrange(anio, mes)[1]
        fecha_inicio = datetime(anio, mes, 1, 0, 0, 0, tzinfo=timezone.utc)
        fecha_fin = datetime(anio, mes, ultimo_dia, 23, 59, 59, tzinfo=timezone.utc)
        vista_mensual = True
    else:
        mes = None
        fecha_inicio = datetime(anio, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        fecha_fin = datetime(anio, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        vista_mensual = False

    date_inicio = date(anio, mes if mes else 1, 1)
    date_fin = date(anio, mes if mes else 12, calendar.monthrange(anio, mes if mes else 12)[1])

    ingresos_data = _calcular_ingresos(fecha_inicio, fecha_fin, vista_mensual, anio, mes)
    asistencias_data = _calcular_asistencias(fecha_inicio, fecha_fin)
    espera_data = _calcular_lista_espera(date_inicio, date_fin)
    ocupacion_data = _calcular_ocupacion_clases(date_inicio, date_fin)

    return {
        "asistencias": asistencias_data,
        "horarios_solicitados": espera_data,
        "ingresos": ingresos_data,
        "ocupacion_clases": ocupacion_data
    }

def _calcular_ingresos(fecha_inicio, fecha_fin, vista_mensual, anio, mes):
    query_pagos = db.session.query(Pago.proveedor, Pago.monto_pagado, Pago.fecha_pago)\
        .filter(or_(Pago.estado == "approved", Pago.estado == "aprobado", Pago.estado == "confirmado"))\
        .filter(Pago.fecha_pago >= fecha_inicio)\
        .filter(Pago.fecha_pago <= fecha_fin)\
        .all()

    ingreso_total = 0.0
    distribucion_pagos = []
    evolucion_ingresos = []

    if vista_mensual:
        dias_mes = list(range(1, calendar.monthrange(anio, mes)[1] + 1))
        df_base = pd.DataFrame({"eje_x_num": dias_mes, "fecha_label": [f"Día {d}" for d in dias_mes]})
    else:
        meses_es = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        df_base = pd.DataFrame({"eje_x_num": range(1, 13), "fecha_label": meses_es})

    if query_pagos:
        df_pagos = pd.DataFrame(query_pagos, columns=["proveedor", "monto_pagado", "fecha_pago"])
        df_pagos["monto_pagado"] = df_pagos["monto_pagado"].apply(lambda x: float(x) if isinstance(x, (Decimal, float)) else 0.0)
        df_pagos["fecha_pago"] = pd.to_datetime(df_pagos["fecha_pago"]).dt.tz_localize(None)
        
        ingreso_total = float(df_pagos["monto_pagado"].sum())
        
        df_resumen_prov = df_pagos.groupby("proveedor", as_index=False)["monto_pagado"].sum()
        distribucion_pagos = df_resumen_prov.to_dict(orient="records")

        df_pagos["eje_x_num"] = df_pagos["fecha_pago"].dt.day if vista_mensual else df_pagos["fecha_pago"].dt.month
        df_temporal = df_pagos.groupby("eje_x_num")["monto_pagado"].sum().reset_index()

        df_proyeccion = pd.merge(df_base, df_temporal, on="eje_x_num", how="left").fillna(0)
        df_proyeccion["monto_pagado"] = df_proyeccion["monto_pagado"].astype(float)
        evolucion_ingresos = df_proyeccion[["fecha_label", "monto_pagado"]].to_dict(orient="records")
    else:
        df_base["monto_pagado"] = 0.0
        evolucion_ingresos = df_base[["fecha_label", "monto_pagado"]].to_dict(orient="records")

    return {
        "total": ingreso_total,
        "por_proveedor": distribucion_pagos,
        "evolucion": evolucion_ingresos 
    }


def _calcular_asistencias(fecha_inicio, fecha_fin):
    total_asistencias = db.session.query(func.count(Asistencia.asistencia_id))\
        .filter(Asistencia.fecha_hora >= fecha_inicio)\
        .filter(Asistencia.fecha_hora <= fecha_fin)\
        .scalar() or 0

    return [{"total_asistencias": total_asistencias}]


def _calcular_lista_espera(date_inicio, date_fin):

    query_espera = db.session.query(Clase.actividad, func.count(ListaEspera.lista_espera_id))\
        .join(ListaEspera, ListaEspera.clase_id == Clase.clase_id)\
        .filter(Clase.fecha >= date_inicio)\
        .filter(Clase.fecha <= date_fin)\
        .group_by(Clase.actividad)\
        .order_by(func.count(ListaEspera.lista_espera_id).desc())\
        .limit(5)\
        .all()

    horarios_solicitados = []
    for actividad_enum, cantidad in query_espera:
        horarios_solicitados.append({
            "label": actividad_enum.value if hasattr(actividad_enum, 'value') else str(actividad_enum),
            "cantidad": cantidad
        })
        
    return horarios_solicitados


def _calcular_ocupacion_clases(date_inicio, date_fin):

    clases_periodo = db.session.query(Clase.clase_id, Clase.actividad, Clase.cupos)\
        .filter(Clase.fecha >= date_inicio)\
        .filter(Clase.fecha <= date_fin)\
        .all()

    ocupacion_map = {}
    for c_id, act, cupos in clases_periodo:
        act_label = act.value if hasattr(act, 'value') else str(act)
        
        reservas_count = db.session.query(func.count(Reserva.reserva_id))\
            .filter(Reserva.clase_id == c_id)\
            .filter(Reserva.estado.in_(["confirmada", "asistida", "confirmado"]))\
            .scalar() or 0
        
        pct = (reservas_count / cupos * 100) if cupos > 0 else 0.0
        pct = min(pct, 100.0)
        
        if act_label not in ocupacion_map:
            ocupacion_map[act_label] = []
        ocupacion_map[act_label].append(pct)

    ocupacion_clases = []
    for act_label, lista_porcentajes in ocupacion_map.items():
        promedio = sum(lista_porcentajes) / len(lista_porcentajes)
        ocupacion_clases.append({
            "clase_label": act_label,
            "porcentaje_ocupacion": round(promedio, 1)
        })
    return ocupacion_clases