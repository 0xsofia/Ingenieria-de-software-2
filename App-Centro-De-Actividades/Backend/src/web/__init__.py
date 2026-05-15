from flask import Flask
from flask import render_template
from flask_cors import CORS
from src.web.handlers import error
from src.core import database
from src.core.config import config
from src.core.seeds import run_seeds
from src.web.controllers.iniciar_sesion import login_bp
from src.web.controllers.registrarse import registrarse_bp
from src.web.controllers.usuarios import usuarios_bp

from src.web.controllers.session_controller import session_bp

from src.core.bcrypt_and_session import bcrypt, cipher, login_manager


def create_app(env="development", static_folder="../../static"):
    app = Flask(__name__, static_folder=static_folder)

    app.config.from_object(config[env])
    database.init_app(app)

    bcrypt.init_app(app)
    login_manager.init_app(app)
    CORS(app, supports_credentials=True)
    cipher.init_app(app)

    @app.route("/")
    def home():
        return render_template("home.html")

    app.register_error_handler(404, error.not_found_error)

    app.register_blueprint(login_bp)
    app.register_blueprint(registrarse_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(session_bp)

    @app.cli.command(name="reset_db")
    def reset_db():
        database.reset()

    @app.cli.command(name="seed_db")
    def seed_db():
        database.ensure_seed_prerequisites()
        run_seeds(app)

    return app
