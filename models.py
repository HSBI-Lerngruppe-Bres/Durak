# models.py
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from database import db

class Spieler(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Spiel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    startzeit = db.Column(db.DateTime, nullable=False)

class SpielZustand(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spielsitzung_id = db.Column(db.String(36), unique=True, nullable=False)
    spieler_haende = db.Column(db.String(500), nullable=False)
    aktueller_spieler_id = db.Column(db.String(50), nullable=False)
    ablage_stapel = db.Column(db.String(500), nullable=False)
    zieh_stapel = db.Column(db.String(500), nullable=False)

class RaumSitzung(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    raum = db.Column(db.String(4), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    beitrittszeit = db.Column(db.DateTime, default=datetime.utcnow)
    verlasszeit = db.Column(db.DateTime)
