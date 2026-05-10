def run_seeds(app):
    with app.app_context():
        from .usuarios import seed_usuarios

        seed_usuarios()
