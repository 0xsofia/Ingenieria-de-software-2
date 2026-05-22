import os
from flask import Flask
from flask_cors import CORS
from src.web import create_app

app = create_app()
if __name__ == '__main__':
    use_ssl = (os.environ.get("FLASK_SSL_ADHOC") or "").strip().lower() in {"1", "true", "yes"}
    app.run(ssl_context="adhoc" if use_ssl else None)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")

    
CORS(app)