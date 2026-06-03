def run_seeds(app, include_reintegros=True):
    with app.app_context():
        from .actividades import seed_actividades
        from .usuarios import seed_usuarios
        from .creditos import seed_creditos
        from .profesores import seed_profesores
        from .clases import (
            get_seed_reference_datetime,
            seed_clases,
            seed_clases_abono_mensual,
        )
        from .pagos import seed_pagos
        from .abonos_mensuales import seed_abonos_mensuales
        from .reservas import seed_reservas
        from .reintegros_escenarios import seed_reintegros_escenarios
        from .escenarios_operativos import seed_escenarios_operativos
        from .metricas import seed_metricas
        from .bloqueos_escenarios import seed_bloqueos_escenarios

        seed_datetime = get_seed_reference_datetime()

        seed_actividades()
        seed_usuarios()
        seed_creditos()
        seed_profesores()
        seed_clases(seed_datetime)
        seed_clases_abono_mensual(seed_datetime)
        seed_abonos_mensuales(seed_datetime)
        seed_pagos()
        seed_reservas(seed_datetime)
        seed_escenarios_operativos(seed_datetime)
        # seed_metricas() 
        seed_bloqueos_escenarios(seed_datetime)

        if include_reintegros:
            seed_reintegros_escenarios(seed_datetime)
