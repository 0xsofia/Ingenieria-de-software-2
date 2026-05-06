from flask import Flask
from flask import render_template
from flask_cors import CORS
from src.web.handlers import error 
from src.core import database
from src.core.config import config
 
from src.web.controllers.session_controller import session_bp 
 
from src.core.bcrypt_and_session import bcrypt, session, cipher
 

def create_app(env="development", static_folder="../../static"):
    app = Flask(__name__, static_folder=static_folder)

    app.config.from_object(config[env])
    database.init_app(app)

    bcrypt.init_app(app)
    session.init_app(app) 
    CORS(app)
    cipher.init_app(app)

    @app.route("/")
    def home():
        return render_template("home.html")

    app.register_error_handler(404, error.not_found_error) 

    app.register_blueprint(session_bp)
 

    @app.cli.command(name="reset-db")
    def reset_db():
        database.reset()

    return app