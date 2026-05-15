def run_seeds(app):
    with app.app_context():
        from .asistencia import seed_asistencia
        from .usuarios import seed_usuarios

        seed_usuarios()
        seed_asistencia()
