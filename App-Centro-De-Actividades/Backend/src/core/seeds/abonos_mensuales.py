from datetime import date, time
import calendar

from src.core.database import db
from src.core.models.abono_mensual import AbonoMensual
from src.core.models.persona import Socio
from src.core.models.actividad import Actividad
from src.core.seeds.clases import get_seed_reference_datetime


def seed_abonos_mensuales(seed_datetime=None):
    seed_datetime = get_seed_reference_datetime(seed_datetime)
    year = seed_datetime.year
    month = seed_datetime.month

    # Periodo del mes actual del seed
    periodo_inicio = date(year, month, 1)
    ultimo_dia = calendar.monthrange(year, month)[1]
    periodo_fin = date(year, month, ultimo_dia)

    fecha_limite_renovacion = date(year, month, min(10, ultimo_dia))

    socios = Socio.query.limit(5).all()
    actividades = Actividad.query.limit(5).all()

    if not socios or not actividades:
        print("[SEED] No hay socios o actividades suficientes para seedear abonos mensuales.")
        return

    created = 0
    for i, socio in enumerate(socios):
        actividad = actividades[i % len(actividades)]

        # usar persona_id como FK del socio
        socio_id = getattr(socio, "persona_id", None)

        # comprobar si ya existe un abono para este socio y actividad en el mismo periodo
        existing = (
            AbonoMensual.query.filter_by(socio_id=socio_id, actividad_id=actividad.actividad_id)
            .filter(AbonoMensual.periodo_inicio == periodo_inicio)
            .first()
        )

        if existing:
            continue

        abono = AbonoMensual(
            socio_id=socio_id,
            actividad_id=actividad.actividad_id,
            periodo_inicio=periodo_inicio,
            periodo_fin=periodo_fin,
            hora_inicio=time(19, 0),
            dia_semana=periodo_inicio.strftime('%A'),
            fecha_limite_renovacion=fecha_limite_renovacion,
            estado='activo',
        )

        db.session.add(abono)
        db.session.flush()
        created += 1

    if created > 0:
        db.session.commit()
        print(f"[SEED] Seeded {created} abonos mensuales.")
    else:
        print("[SEED] No se crearon nuevos abonos mensuales.")
