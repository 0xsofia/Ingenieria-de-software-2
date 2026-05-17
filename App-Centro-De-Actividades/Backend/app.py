import os

from src.web import create_app

app = create_app()
if __name__ == '__main__':
    use_ssl = (os.environ.get("FLASK_SSL_ADHOC") or "").strip().lower() in {"1", "true", "yes"}
    app.run(ssl_context="adhoc" if use_ssl else None)
    