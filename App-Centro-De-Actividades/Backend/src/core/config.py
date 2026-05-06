from os import environ
from os import environ
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv(dotenv_path='.env')

class Config(object):
    TESTING = False
    SESSION_TYPE= "filesystem"
    SESSION_PERMANENT= True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    
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

config = {
    "development" : DevelopmentConfig,
    "production" : ProductionConfig,
    "testing" : TestingConfig
}