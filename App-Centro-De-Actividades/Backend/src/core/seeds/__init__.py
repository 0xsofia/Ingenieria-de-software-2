def run_seeds(app):
    with app.app_context():
        from .usuarios import seed_usuarios
        from .profesores import seed_profesores
        from .clases import seed_clases

        seed_usuarios()
        seed_profesores()
        seed_clases()
