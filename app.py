# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room, send
from database import db
from flask_migrate import Migrate
import random
from string import ascii_uppercase
from datetime import datetime
import uuid
import os
from flask_bcrypt import Bcrypt
import socket

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:\\Users\\Benjamin\\Desktop\\Durak - 04_06\\instance\\spiel.db'
app.config['SECRET_KEY'] = 'geheimeschluessel'
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SECURE'] = True

socketio = SocketIO(app)

db.init_app(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)

with app.app_context():
    db.create_all()

from models import Spieler, Spiel, SpielZustand, RaumSitzung

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        user = Spieler.query.filter_by(email=email).first()
        if user:
            flash('E-Mail bereits registriert')
            return redirect(url_for('register'))
        try:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            new_user = Spieler(name=name, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registrierung erfolgreich! Bitte melden Sie sich an.')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Fehler bei der Registrierung: ' + str(e))
            return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = Spieler.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('Erfolgreich angemeldet!')
            return redirect(url_for('index'))
        else:
            flash('Ungültige E-Mail oder Passwort')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Erfolgreich abgemeldet!')
    return redirect(url_for('welcome'))

@app.route('/welcome')
def welcome():
    return render_template('welcome.html')

#------------------------------------------------------------------------------------------------------------------------------------------
rooms = {}

def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        
        if code not in rooms:
            break
    
    return code

# Die Trumpffarbe für das Spiel wird einmal festgelegt
def generate_trumpf():
    return random.choice(['C', 'D', 'H', 'S'])  # Kreuz, Karo, Herz, Pik

def generate_deck():
    ranks = ['6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    suits = ['C', 'D', 'H', 'S']  # Kreuz, Karo, Herz, Pik
    deck = [{'rank': rank, 'suit': suit} for rank in ranks for suit in suits]
    random.shuffle(deck)
    return deck

@app.route('/multiplayer', methods=['POST', 'GET'])
def multiplayer():
    session.clear()
    if request.method =='POST':
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        if not name:
            return render_template("multiplayer.html", error="Please enter a name.", code=code, name=name)

        if join != False and not code:
            return render_template("multiplayer.html", error="Please enter a room code.", code=code, name=name)
        
        room = code
        if create != False:
            room = generate_unique_code(4)
            trumpf = generate_trumpf()
            deck = generate_deck()
            rooms[room] = {"members": 0, "trumpf": trumpf, "deck": deck, "hands": {}}

        elif code not in rooms:
            return render_template("multiplayer.html", error="Room does not exist.", code=code, name=name)

        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))

    return render_template('multiplayer.html')

@app.route("/room")
def room():
    room = session.get("room")
    name = session.get("name")
    if room is None or name is None or room not in rooms:
        return redirect(url_for("multiplayer"))
    
    trumpf = rooms[room]["trumpf"]

    if name not in rooms[room]["hands"]:
        rooms[room]["hands"][name] = rooms[room]["deck"][:6]
        rooms[room]["deck"] = rooms[room]["deck"][6:]

    player_hand = rooms[room]["hands"][name]

    return render_template("spielfeld.html", code=room, trumpf=trumpf, deck=player_hand)

@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return
    
    join_room(room)
    send({"name": name, "message": "has entered the gameroom"}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} joined room {room}")

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]
    
    send({"name": name, "message": "has left the room"}, to=room)
    print(f"{name} has left the room {room}")

if __name__ == "__main__":
    socketio.run(app, debug=True)
