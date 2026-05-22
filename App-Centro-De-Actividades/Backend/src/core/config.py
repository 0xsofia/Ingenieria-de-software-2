from os import environ
from pathlib import Path

from dotenv import load_dotenv
from datetime import timedelta
from cryptography.fernet import Fernet

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(dotenv_path=_BACKEND_ROOT / '.env')


def _get_int_env(name, default):
    value = environ.get(name)
    if value in (None, ''):
        return default
    return int(value)

class Config(object):
    TESTING = False
    SECRET_KEY = environ.get('SECRET_KEY', 'development-secret-key')
    SESSION_PERMANENT= True
    SESSION_COOKIE_SAMESITE = "None"
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAILJET_SMTP_HOST = environ.get('MAILJET_SMTP_HOST', 'in-v3.mailjet.com')
    MAILJET_SMTP_PORT = _get_int_env('MAILJET_SMTP_PORT', 587)
    MAILJET_SMTP_TIMEOUT = _get_int_env('MAILJET_SMTP_TIMEOUT', 15)
    MAILJET_API_KEY = environ.get('MAILJET_API_KEY', environ.get('MJ_APIKEY_PUBLIC', ''))
    MAILJET_SECRET_KEY = environ.get('MAILJET_SECRET_KEY', environ.get('MJ_APIKEY_PRIVATE', ''))
    MAILJET_SENDER_DOMAIN = environ.get('MAILJET_SENDER_DOMAIN', '')
    MAILJET_SENDER_LOCAL_PART = environ.get('MAILJET_SENDER_LOCAL_PART', 'no-reply')
    MAILJET_SENDER_EMAIL = environ.get('MAILJET_SENDER_EMAIL', '')
    MAILJET_SENDER_NAME = environ.get('MAILJET_SENDER_NAME', 'Centro de Actividades')
    FRONTEND_LOGIN_URL = environ.get('FRONTEND_LOGIN_URL', 'http://localhost:5173/login')
    
class ProductionConfig(Config):
    db_url = environ.get("DATABASE_URL")
    
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        
    SQLALCHEMY_DATABASE_URI = db_url

class DevelopmentConfig(Config):
    ...
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = "None"
    DB_USER = environ.get('DB_USER')
    DB_PASSWORD = environ.get('DB_PASSWORD')
    DB_HOST = environ.get('DB_HOST')
    DB_PORT = environ.get('DB_PORT')
    DB_NAME = environ.get('DB_NAME')
    SQLALCHEMY_DATABASE_URI = (f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    FERNET_KEY = environ.get('FERNET_KEY')


class TestingConfig(Config):
    TESTING = True
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = "Lax"
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    FERNET_KEY = Fernet.generate_key().decode('utf-8')

config = {
    "development" : DevelopmentConfig,
    "production" : ProductionConfig,
    "testing" : TestingConfig
}
