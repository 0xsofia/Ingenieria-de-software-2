from os import environ
from dotenv import load_dotenv
from datetime import timedelta
from cryptography.fernet import Fernet

load_dotenv(dotenv_path='.env')

class Config(object):
    TESTING = False
    SECRET_KEY = environ.get('SECRET_KEY', 'development-secret-key')
    SESSION_PERMANENT= True
    SESSION_COOKIE_SAMESITE = "None"
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
class ProductionConfig(Config):
    ...

class DevelopmentConfig(Config):
    ...
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
