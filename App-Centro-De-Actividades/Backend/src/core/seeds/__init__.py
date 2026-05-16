def run_seeds(app):
    with app.app_context():
        from .usuarios import seed_usuarios
        from .profesores import seed_profesores

        seed_usuarios()
        seed_profesores()
