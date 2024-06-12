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
from functools import wraps

# Füge das aktuelle Verzeichnis und das Elterndirektorium zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

basedir = os.path.abspath(os.path.dirname(__file__))

from database import db
from models import Spieler, Spiel, SpielZustand, RaumSitzung

# db init
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'spiel.db')
app.config['SECRET_KEY'] = 'geheimeschluessel'
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SECURE'] = True

db.init_app(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
socketio = SocketIO(app)

with app.app_context():
    db.create_all()

# login and registration handling
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Bitte melden Sie sich an, um auf diese Seite zuzugreifen.')
            return redirect(url_for('welcome'))
        return f(*args, **kwargs)
    return decorated_function

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
@login_required
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

# game handling
def generate_trumpf():
    return random.choice(['C', 'D', 'H', 'S'])

def rank_value(rank):
    rank_order = ['6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    return rank_order.index(rank)

def generate_deck():
    ranks = ['6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    suits = ['C', 'D', 'H', 'S']
    deck = [{'rank': rank, 'suit': suit} for rank in ranks for suit in suits]
    random.shuffle(deck)
    return deck

def draw_cards(room):
    for player in rooms[room]['hands']:
        while len(rooms[room]['hands'][player]) < 6 and rooms[room]['draw_pile']:
            rooms[room]['hands'][player].append(rooms[room]['draw_pile'].pop())
            emit('update_hand', {'hand': rooms[room]['hands'][player]}, room=player)

@app.route('/multiplayer', methods=['POST', 'GET'])
def multiplayer():
    if request.method == 'POST':
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
            if 'user_id' not in session:
                flash('Bitte melden Sie sich an, um ein Spiel zu erstellen.')
                return redirect(url_for('welcome'))
            
            room = generate_unique_code(4)
            trumpf = generate_trumpf()
            deck = generate_deck()
            rooms[room] = {"members": 0, "trumpf": trumpf, "deck": deck, "hands": {}, "game_started": False, "draw_pile": [], "sids": {}, "placements": {}, "current_player": None, "defender": None}

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
        rooms[room]["hands"][name] = []
        rooms[room]["members"] += 1

    player_hand = rooms[room]["hands"][name]

    return render_template("spielfeld.html", code=room, trumpf=trumpf, deck=player_hand)

@socketio.on('start_game')
def handle_start_game():
    room = session.get('room')
    if room and room in rooms:
        rooms[room]['game_started'] = True
        emit('message', {'name': 'System', 'message': 'Das Spiel hat begonnen!'}, room=room)

        # Karten austeilen
        for player in rooms[room]['hands']:
            rooms[room]['hands'][player] = rooms[room]['deck'][:6]
            rooms[room]['deck'] = rooms[room]['deck'][6:]

        # Ziehstapel initialisieren
        rooms[room]['draw_pile'] = rooms[room]['deck']
        rooms[room]['deck'] = []

        # Initialisieren der gespielten Karten
        rooms[room]['played_cards'] = []

        # Spieler über ihre Hände informieren
        for player, hand in rooms[room]['hands'].items():
            if player in rooms[room]['sids']:
                for sid in rooms[room]['sids'][player]:
                    emit('update_hand', {'hand': hand}, room=sid)

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
        defender_index = (list(rooms[room]['hands'].keys()).index(player_with_lowest_trump) + 1) % len(rooms[room]['hands'])
        rooms[room]['defender'] = list(rooms[room]['hands'].keys())[defender_index]
        emit('start_player', {'player': player_with_lowest_trump}, room=room)
        print(f"Game started in room {room} with player {player_with_lowest_trump} as attacker and {rooms[room]['defender']} as defender")

@socketio.on('join')
def on_join(data):
    room = session.get('room')
    name = session.get('name')
    if room and name:
        if name not in rooms[room]['sids']:
            join_room(room)
            rooms[room]['members'] += 1
            rooms[room]['hands'][name] = []
            rooms[room]['sids'][name] = [request.sid]
            emit('message', {'name': name, 'message': 'has entered the gameroom'}, room=room)
        elif request.sid not in rooms[room]['sids'][name]:
            rooms[room]['sids'][name].append(request.sid)
            join_room(room)

def check_winner(room):
    players_with_no_cards = [player for player, hand in rooms[room]['hands'].items() if not hand]
    if players_with_no_cards:
        for player in players_with_no_cards:
            if player not in rooms[room]['placements']:
                rooms[room]['placements'][player] = len(rooms[room]['placements']) + 1
                emit('message', {'name': 'System', 'message': f'{player} hat Platz {rooms[room]["placements"][player]} belegt!'}, room=room)
                rooms[room]['hands'].pop(player)

        if len(rooms[room]['placements']) == rooms[room]['members'] - 1:
            for player in rooms[room]['hands']:
                if player not in rooms[room]['placements']:
                    rooms[room]['placements'][player] = 'Verlierer'
                    emit('message', {'name': 'System', 'message': f'{player} ist der Verlierer!'}, room=room)
            emit('game_over', {'placements': rooms[room]['placements']}, room=room)
            rooms[room]['game_started'] = False

@socketio.on('play_card')
def handle_play_card(data):
    room = session.get('room')
    name = session.get('name')
    if room and name and room in rooms:
        if not rooms[room].get('game_started', False):
            emit('message', {'name': 'System', 'message': 'Das Spiel hat noch nicht begonnen. Bitte warten Sie, bis das Spiel gestartet ist.'}, room=request.sid)
            return

        card = {'rank': data['rank'], 'suit': data['suit']}
        current_player = rooms[room]['current_player']
        defender = rooms[room]['defender']
        players = [player for player in rooms[room]['hands'] if rooms[room]['hands'][player]]

        if card in rooms[room]['hands'][name]:
            if name == current_player:
                if 'played_cards' not in rooms[room]:
                    rooms[room]['played_cards'] = []

                if len(rooms[room]['played_cards']) < len(rooms[room]['hands'][defender]):
                    # Prüfen, ob der Angreifer nur Karten des gleichen Rangs spielt
                    if rooms[room].get('played_cards'):
                        valid_ranks = {c['rank'] for group in rooms[room]['played_cards'] for c in group}
                        if card['rank'] not in valid_ranks:
                            emit('message', {'name': 'System', 'message': 'Ungültiger Zug. Du kannst nur Karten des gleichen Rangs spielen.'}, room=request.sid)
                            return

                    rooms[room]['hands'][name].remove(card)
                    rooms[room]['played_cards'].append([card])

                    emit('update_hand', {'hand': rooms[room]['hands'][name]}, room=request.sid)
                    emit('card_played', {'rank': card['rank'], 'suit': card['suit'], 'player': name}, room=room)
                    emit('update_played_cards', {'played_cards': rooms[room]['played_cards']}, room=room)
                    check_winner(room)
                else:
                    emit('message', {'name': 'System', 'message': 'Ungültiger Zug. Du kannst nicht mehr Karten spielen, als der Verteidiger Karten hat.'}, room=request.sid)
            else:
                # Logik für Mitangreifer
                if name != defender:
                    if 'played_cards' in rooms[room] and rooms[room]['played_cards']:
                        valid_ranks = {c['rank'] for group in rooms[room]['played_cards'] for c in group}
                        if card['rank'] in valid_ranks:
                            if len(rooms[room]['played_cards']) < len(rooms[room]['hands'][defender]):
                                rooms[room]['hands'][name].remove(card)
                                rooms[room]['played_cards'].append([card])
                                emit('update_hand', {'hand': rooms[room]['hands'][name]}, room=request.sid)
                                emit('card_played', {'rank': card['rank'], 'suit': card['suit'], 'player': name}, room=room)
                                emit('update_played_cards', {'played_cards': rooms[room]['played_cards']}, room=room)
                            else:
                                emit('message', {'name': 'System', 'message': 'Ungültiger Zug. Du kannst nicht mehr Karten spielen, als der Verteidiger Karten hat.'}, room=request.sid)
                        else:
                            emit('message', {'name': 'System', 'message': 'Ungültiger Zug. Du kannst nur Karten des gleichen Rangs spielen.'}, room=request.sid)
                    else:
                        emit('message', {'name': 'System', 'message': 'Ungültiger Zug. Du kannst nur Karten des gleichen Rangs spielen.'}, room=request.sid)
                else:
                    emit('message', {'name': 'System', 'message': 'Verteidiger kann keine Karten legen.'}, room=request.sid)
        else:
            emit('message', {'name': 'System', 'message': 'Ungültiger Zug. Diese Karte ist nicht in deiner Hand.'}, room=request.sid)

@socketio.on('overplay_card')
def handle_overplay_card(data):
    room = session.get('room')
    name = session.get('name')
    if room and name:
        if not rooms[room].get('game_started', False):
            emit('message', {'name': 'System', 'message': 'Das Spiel hat noch nicht begonnen. Bitte warten Sie, bis das Spiel gestartet ist.'}, room=request.sid)
            return

        current_player = rooms[room]['current_player']
        defender = rooms[room]['defender']
        players = [player for player in rooms[room]['hands'] if rooms[room]['hands'][player]]
        card = {'rank': data['rank'], 'suit': data['suit']}
        target_index = data.get('target_index')
        trumpf = rooms[room]['trumpf']

        if name == defender:  # Nur der Verteidiger darf Karten überlagern
            if target_index is not None and 0 <= target_index < len(rooms[room]['played_cards']):
                if card in rooms[room]['hands'][name]:
                    target_card = rooms[room]['played_cards'][target_index][-1]

                    if (card['suit'] == target_card['suit'] and rank_value(card['rank']) > rank_value(target_card['rank'])) or (card['suit'] == trumpf and target_card['suit'] != trumpf):
                        rooms[room]['hands'][name].remove(card)
                        rooms[room]['played_cards'][target_index].append(card)
                        emit('update_hand', {'hand': rooms[room]['hands'][name]}, room=request.sid)
                        emit('card_overplayed', {'rank': card['rank'], 'suit': card['suit'], 'player': name, 'target_index': target_index}, room=room)
                        check_winner(room)
                    elif card['suit'] == trumpf and target_card['suit'] == trumpf and rank_value(card['rank']) > rank_value(target_card['rank']):
                        rooms[room]['hands'][name].remove(card)
                        rooms[room]['played_cards'][target_index].append(card)
                        emit('update_hand', {'hand': rooms[room]['hands'][name]}, room=request.sid)
                        emit('card_overplayed', {'rank': card['rank'], 'suit': card['suit'], 'player': name, 'target_index': target_index}, room=room)
                        check_winner(room)
                    else:
                        emit('message', {'name': 'System', 'message': 'Ungültiger Zug. Diese Karte kann die Zielkarte nicht schlagen.'}, room=request.sid)
                else:
                    emit('message', {'name': 'System', 'message': 'Ungültiger Zug. Diese Karte ist nicht in deiner Hand.'}, room=request.sid)
            else:
                emit('message', {'name': 'System', 'message': 'Ungültiger Zug. Ungültiges Ziel.'}, room=request.sid)
        else:
            emit('message', {'name': 'System', 'message': 'Nur der Verteidiger darf Karten überlagern.'}, room=request.sid)

@socketio.on('end_attack')
def handle_end_attack():
    room = session.get('room')
    name = session.get('name')
    if room and name:
        current_player = rooms[room]['current_player']
        defender = rooms[room]['defender']
        if name == current_player:
            if 'played_cards' in rooms[room] and any(len(group) == 1 for group in rooms[room]['played_cards']):
                emit('message', {'name': 'System', 'message': 'Nicht alle Karten wurden geschlagen. Du kannst den Angriff nicht beenden.'}, room=request.sid)
                return

            if 'played_cards' in rooms[room] and rooms[room]['played_cards']:
                rooms[room]['played_cards'] = []
                emit('clear_played_cards', room=room)

            # Nachziehen der Karten für alle Spieler
            for player in rooms[room]['hands']:
                while len(rooms[room]['hands'][player]) < 6 and rooms[room]['draw_pile']:
                    rooms[room]['hands'][player].append(rooms[room]['draw_pile'].pop())
                for sid in rooms[room]['sids'][player]:
                    emit('update_hand', {'hand': rooms[room]['hands'][player]}, room=sid)

            # Der Verteidiger bleibt Verteidiger, der nächste Spieler wird neuer Angreifer
            if rooms[room]['hands'][current_player]:
                players = [player for player in rooms[room]['hands'] if rooms[room]['hands'][player]]
                current_index = players.index(current_player)
                next_index = (current_index + 1) % len(players)
                rooms[room]['current_player'] = players[next_index]
            else:
                players = [player for player in rooms[room]['hands'] if rooms[room]['hands'][player]]
                defender_index = players.index(defender)
                next_index = (defender_index + 1) % len(players)
                rooms[room]['current_player'] = players[next_index]

            emit('update_current_player', {'current_player': rooms[room]['current_player']}, room=room)
            emit('message', {'name': 'System', 'message': f'{name} hat den Angriff beendet. Nächster Spieler ist {rooms[room]["current_player"]}.'}, room=room)

            check_winner(room)
        else:
            emit('message', {'name': 'System', 'message': 'Nur der Angreifer kann den Angriff beenden.'}, room=request.sid)

@socketio.on('take_cards')
def handle_take_cards():
    room = session.get('room')
    name = session.get('name')
    if room and name:
        current_player = rooms[room]['current_player']
        defender = rooms[room]['defender']
        players = [player for player in rooms[room]['hands'] if rooms[room]['hands'][player]]

        if name == defender:
            if 'played_cards' in rooms[room] and all(len(group) == 2 for group in rooms[room]['played_cards']):
                emit('message', {'name': 'System', 'message': 'Du hast alle Karten geschlagen. Du kannst die Karten nicht nehmen.'}, room=request.sid)
                return

            # Verteidiger nimmt die Karten
            rooms[room]['hands'][name].extend([card for group in rooms[room]['played_cards'] for card in group])
            rooms[room]['played_cards'] = []
            emit('update_hand', {'hand': rooms[room]['hands'][name]}, room=request.sid)
            emit('clear_played_cards', room=room)
            emit('message', {'name': 'System', 'message': f'{name} hat die Karten genommen.'}, room=room)

            # Nachziehen der Karten für alle Spieler
            for player in rooms[room]['hands']:
                while len(rooms[room]['hands'][player]) < 6 and rooms[room]['draw_pile']:
                    rooms[room]['hands'][player].append(rooms[room]['draw_pile'].pop())
                for sid in rooms[room]['sids'][player]:
                    emit('update_hand', {'hand': rooms[room]['hands'][player]}, room=sid)

            # Verteidiger bleibt Verteidiger, der nächste Spieler nach dem Verteidiger wird neuer Angreifer
            next_index = (players.index(defender) + 1) % len(players)
            rooms[room]['current_player'] = players[next_index]

            emit('update_current_player', {'current_player': rooms[room]['current_player']}, room=room)

            check_winner(room)
        else:
            emit('message', {'name': 'System', 'message': 'Nur der Verteidiger kann die Karten nehmen.'}, room=request.sid)

# session handling
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

    if name not in rooms[room]['sids']:
        join_room(room)
        rooms[room]['sids'][name] = [request.sid]
        rooms[room]['members'] += 1
        send({"name": name, "message": "has entered the gameroom"}, to=room)
        print(f"{name} joined room {room}")
    elif request.sid not in rooms[room]['sids'][name]:
        rooms[room]['sids'][name].append(request.sid)
        join_room(room)

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
        if name in rooms[room]['sids']:
            rooms[room]['sids'][name].remove(request.sid)
            if not rooms[room]['sids'][name]:
                del rooms[room]['sids'][name]
                rooms[room]["members"] -= 1
                if rooms[room]["members"] <= 0:
                    del rooms[room]
        send({"name": name, "message": "has left the room"}, to=room)
        print(f"{name} has left the room {room}")

    try:
        session_entry = RaumSitzung.query.filter_by(raum=room, name=name).order_by(RaumSitzung.beitrittszeit.desc()).first()
        if session_entry:
            session_entry.verlasszeit = datetime.utcnow()
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error updating session in the database: {e}")

# check saving values in the db
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
