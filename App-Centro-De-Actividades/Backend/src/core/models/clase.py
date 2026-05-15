from ...core.database import db
class Clase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    horario_inicio = db.Column(db.DateTime, nullable=False)