# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room, send
from flask_migrate import Migrate
import random
from string import ascii_uppercase
from datetime import datetime
import os
from flask_bcrypt import Bcrypt
import sys
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_migrate import Migrate
import random
from string import ascii_uppercase
from datetime import datetime

# Füge das aktuelle Verzeichnis und das Elterndirektorium zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import db
from models import Spieler, Spiel, SpielZustand, RaumSitzung

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:\\Users\\Benjamin\\Desktop\\durak_06_06\\instance\\spiel.db'
app.config['SECRET_KEY'] = 'geheimeschluessel'
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SECURE'] = True


db.init_app(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
socketio = SocketIO(app)


#########################


with app.app_context():
    db.create_all()

#########################




@app.route('/')
def welcome():
    return render_template('welcome.html')

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

@app.route('/index')
def index():
    return render_template('index.html')

rooms = {}

def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        
        if code not in rooms:
            break
    
    return code

def generate_trumpf():
    return random.choice(['C', 'D', 'H', 'S'])

# Eine Funktion, um den Wert eines Kartenrangs zu ermitteln
def rank_value(rank):
    rank_order = ['6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    return rank_order.index(rank)

def generate_deck():
    ranks = ['6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    suits = ['C', 'D', 'H', 'S']
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
            rooms[room] = {"members": 0, "trumpf": trumpf, "deck": deck, "hands": {}, "game_started": False}

        elif code not in rooms:
            return render_template("multiplayer.html", error="Room does not exist.", code=code, name=name)
        elif rooms[code].get("game_started", False):
            return render_template("multiplayer.html", error="The game has already started, please choose another Gameroom or create a new one.", code=code, name=name)


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

@socketio.on('start_game')
def handle_start_game():
    room = session.get('room')
    if room and room in rooms:
        rooms[room]['game_started'] = True
        emit('message', {'name': 'System', 'message': 'Das Spiel hat begonnen!'}, room=room)
        
        # Ermittlung des Startspielers
        trumpf = rooms[room]['trumpf']
        player_with_lowest_trump = None
        lowest_trump_card = None

        for player, hand in rooms[room]['hands'].items():
            player_trumps = [card for card in hand if card['suit'] == trumpf]
            if player_trumps:
                player_lowest_trump = min(player_trumps, key=lambda card: rank_value(card['rank']))
                if (lowest_trump_card is None or 
                        rank_value(player_lowest_trump['rank']) < rank_value(lowest_trump_card['rank'])):
                    lowest_trump_card = player_lowest_trump
                    player_with_lowest_trump = player

        if player_with_lowest_trump is None:
            # Wenn keiner der Spieler eine Trumpfkarte hat, wählen wir zufällig einen Spieler
            player_with_lowest_trump = random.choice(list(rooms[room]['hands'].keys()))
        
        rooms[room]['current_player'] = player_with_lowest_trump
        emit('start_player', {'player': player_with_lowest_trump}, room=room)
        print(f"Game started in room {room} with player {player_with_lowest_trump}")

@socketio.on('play_card')
def handle_play_card(data):
    room = session.get('room')
    name = session.get('name')
    if room and name:
        card = {'rank': data['rank'], 'suit': data['suit']}
        if card in rooms[room]['hands'][name]:
            rooms[room]['hands'][name].remove(card)
            if 'played_cards' not in rooms[room]:
                rooms[room]['played_cards'] = []
            rooms[room]['played_cards'].append(card)
            emit('card_played', {'rank': card['rank'], 'suit': card['suit'], 'player': name}, room=room)
            emit('update_played_cards', {'played_cards': rooms[room]['played_cards']}, room=room)
        else:
            emit('message', {'name': 'System', 'message': 'Ungültiger Zug. Diese Karte ist nicht in deiner Hand.'}, room=name)

@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return
    if room not in rooms or rooms[room].get('game_started', False):
        emit('redirect', {'url': url_for('multiplayer')})
        return
    
    join_room(room)
    send({"name": name, "message": "has entered the gameroom"}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} joined room {room}")
    
    # Add session entry to the database
    try:
        new_session = RaumSitzung(raum=room, name=name)
        db.session.add(new_session)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error adding session to the database: {e}")

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
    
    # Update session end time in the database
    try:
        session_entry = RaumSitzung.query.filter_by(raum=room, name=name).order_by(RaumSitzung.beitrittszeit.desc()).first()
        if session_entry:
            session_entry.verlasszeit = datetime.utcnow()
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error updating session in the database: {e}")


@app.route('/check_db')
def check_db():
    sessions = RaumSitzung.query.all()
    return jsonify([{
        'id': session.id,
        'raum': session.raum,
        'name': session.name,
        'beitrittszeit': session.beitrittszeit,
        'verlasszeit': session.verlasszeit
    } for session in sessions])


if __name__ == "__main__":
    socketio.run(app, debug=True)
