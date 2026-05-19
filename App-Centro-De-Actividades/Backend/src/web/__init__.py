from flask import Flask
from flask import render_template
from flask_cors import CORS
import os
from src.web.handlers import error
from src.core import database
from src.core.config import config
from src.core.seeds import run_seeds
from src.web.controllers.iniciar_sesion import login_bp
from src.web.controllers.registrarse import registrarse_bp
from src.web.controllers.usuarios import usuarios_bp
from src.web.controllers.escanear_qr import escanearQR_bp   
from src.web.controllers.generar_qr import generar_token_asistencia_bp  

from src.web.controllers.session_controller import session_bp
from src.web.controllers.perfil_controller import perfil_bp
from src.web.controllers.actividad_controller import actividad_bp
from src.web.controllers.clase_controller import clase_bp
from src.web.controllers.profesor_controller import profesor_bp
from src.web.controllers.reservas import reservas_bp
from src.web.controllers.pagos_controller import pagos_bp

from src.core.bcrypt_and_session import bcrypt, cipher, login_manager


def create_app(env="development", static_folder="../../static"):
    app = Flask(__name__, static_folder=static_folder)

    app.config.from_object(config[env])
    database.init_app(app)

    bcrypt.init_app(app)
    login_manager.init_app(app)
    frontend_origin = (os.environ.get("FRONTEND_BASE_URL") or "").rstrip("/")
    allowed_origins = [
        origin
        for origin in {
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            frontend_origin,
        }
        if origin
    ]

    CORS(
        app,
        supports_credentials=True,
        resources={r"/api/*": {"origins": allowed_origins}},
    )
    cipher.init_app(app)

    @app.route("/")
    def home():
        return render_template("home.html")

    app.register_error_handler(404, error.not_found_error)

    app.register_blueprint(login_bp)
    app.register_blueprint(registrarse_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(session_bp)
    app.register_blueprint(perfil_bp)
    app.register_blueprint(actividad_bp)
    app.register_blueprint(clase_bp)
    app.register_blueprint(profesor_bp)
    app.register_blueprint(reservas_bp)
    app.register_blueprint(escanearQR_bp)
    app.register_blueprint(generar_token_asistencia_bp) 
    app.register_blueprint(pagos_bp)

    @app.cli.command(name="reset_db")
    def reset_db():
        database.reset()

    @app.cli.command(name="seed_db")
    def seed_db():
        database.ensure_seed_prerequisites()
        run_seeds(app)

    return app
