def run_seeds(app):
    with app.app_context():
        from .actividades import seed_actividades
        from .usuarios import seed_usuarios
        from .profesores import seed_profesores
        from .clases import seed_clases
        from .reservas import seed_reservas

        seed_actividades()
        seed_usuarios()
        seed_profesores()
        seed_clases()
        seed_reservas()
