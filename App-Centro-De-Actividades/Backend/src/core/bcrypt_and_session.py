import base64
import random
import string
from flask_bcrypt import Bcrypt
from flask_session import Session

from cryptography.fernet import Fernet

session = Session()
bcrypt = Bcrypt()

class Cipher:
    def __init__(self,app = None):
        self.fernet = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        key = base64.urlsafe_b64decode(app.config["FERNET_KEY"])

        self.fernet = Fernet(key)

        app.cipher = self

        return self
    
    def encrypt(self, data: bytes):
        return self.fernet.encrypt(data)
    
    def decrypt(self, data: bytes):
        return self.fernet.decrypt(data)

    def compare(self, data, encrypted):
        return data == self.decrypt(encrypted).decode('utf-8')

    def generate_word(self, length = 6):
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))

cipher = Cipher()