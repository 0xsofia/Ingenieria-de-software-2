def run_seeds(app, include_reintegros=True):
    with app.app_context():
        from .actividades import seed_actividades
        from .usuarios import seed_usuarios
        from .creditos import seed_creditos
        from .profesores import seed_profesores
        from .clases import get_seed_reference_datetime, seed_clases
        from .pagos import seed_pagos
        from .reservas import seed_reservas
        from .reintegros_escenarios import seed_reintegros_escenarios

        seed_datetime = get_seed_reference_datetime()

        seed_actividades()
        seed_usuarios()
        seed_creditos()
        seed_profesores()
        seed_clases(seed_datetime)
        seed_pagos()
        seed_reservas(seed_datetime)

        if include_reintegros:
            seed_reintegros_escenarios(seed_datetime)
