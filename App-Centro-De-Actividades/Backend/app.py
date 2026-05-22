from src.web import create_app

app = create_app()

# 🚀 MIDDLEWARE DE SEGURIDAD DEFINITIVO PARA CORS EN RENDER
class CORSMiddleware(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        # Detectamos el origen de la petición (tu frontend de React)
        origin = environ.get('HTTP_ORIGIN', '')
        allowed_origins = [
            "https://ingenieria-de-software-2-1.onrender.com",
            "http://localhost:5173",
            "http://127.0.0.1:5173"
        ]

        # Si el método es OPTIONS (Preflight), respondemos directo a nivel de servidor
        if environ.get('REQUEST_METHOD') == 'OPTIONS' and origin in allowed_origins:
            status = '200 OK'
            headers = [
                ('Access-Control-Allow-Origin', origin),
                ('Access-Control-Allow-Credentials', 'true'),
                # ('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS'),
                # ('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With, Accept'),
                # Modificá los dos lugares donde aparece 'Access-Control-Allow-Headers' para que queden así:
                ('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With, Accept, ngrok-skip-browser-warning')
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