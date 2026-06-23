import os  # IMPORTANTE: Asegurate de importar os si no estaba arriba
from src.web import create_app

app = create_app()

class CORSMiddleware(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        origin = environ.get('HTTP_ORIGIN', '')
        
        # Traemos la URL configurada en el .env del backend
        env_origin = os.getenv("FRONTEND_BASE_URL")

        allowed_origins = [
            "https://xthzck49-5173.brs.devtunnels.ms",
            "https://ingenieria-de-software-2-1.onrender.com",
            "https://pcverde-linux.tail9449ba.ts.net",
            "http://localhost:5137",
            "http://127.0.0.1:5137",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            # Tu túnel actual (con y sin el puerto explícito por si el navegador lo manda de ambas formas)
            "https://3fbh3v7t-5173.brs.devtunnels.ms",
            "https://3fbh3v7t.brs.devtunnels.ms:5173"
        ]
        
        # Si la URL del .env existe y no está en la lista, la sumamos dinámicamente
        if env_origin and env_origin not in allowed_origins:
            allowed_origins.append(env_origin)

        # Agregamos también la versión con puerto explícito por las dudas
        if env_origin and env_origin.endswith(".ms") and f"{env_origin}:5173" not in allowed_origins:
            # Transforma de 'https://3fbh3v7t-5173.brs.devtunnels.ms' a 'https://3fbh3v7t.brs.devtunnels.ms:5173' si hiciera falta
            clean_tunnel = env_origin.replace("-5173", "")
            allowed_origins.append(f"{clean_tunnel}:5173")

        if environ.get('REQUEST_METHOD') == 'OPTIONS' and origin in allowed_origins:
            status = '200 OK'
            headers = [
                ('Access-Control-Allow-Origin', origin),
                ('Access-Control-Allow-Credentials', 'true'),
                ('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS'),
                ('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With, Accept, ngrok-skip-browser-warning'),
                ('Content-Length', '0')
            ]
            start_response(status, headers)
            return [b'']

        # Para el resto de las peticiones (POST, GET, etc.), inyectamos las cabeceras a la respuesta de Flask
        def custom_start_response(status, headers, exc_info=None):
            if origin in allowed_origins:
                # Removemos duplicados si Flask intentó meterlos antes
                headers = [h for h in headers if h[0].lower() not in (
                    'access-control-allow-origin', 
                    'access-control-allow-credentials',
                    'access-control-allow-methods',
                    'access-control-allow-headers'
                )]
                # Forzamos los valores correctos
                headers.append(('Access-Control-Allow-Origin', origin))
                headers.append(('Access-Control-Allow-Credentials', 'true'))
                headers.append(('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS'))
                headers.append(('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With, Accept'))
            return start_response(status, headers, exc_info)

        return self.app(environ, custom_start_response)

# Inyectamos el middleware sobre la aplicación de Flask
app.wsgi_app = CORSMiddleware(app.wsgi_app)