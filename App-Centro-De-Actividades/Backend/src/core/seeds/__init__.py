def run_seeds(app):
    with app.app_context():
        from .clases import seed_clases
        from .usuarios import seed_usuarios

        seed_usuarios()
        seed_clases()
