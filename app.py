# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_socketio import SocketIO, emit, join_room, leave_room
from database import db
from flask_migrate import Migrate
import random
import json
from datetime import datetime
import uuid
import os
from flask_bcrypt import Bcrypt

app = Flask(__name__, static_folder='static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:\\Users\\Benjamin\\Desktop\\durak_projekt\\instance\\spiel.db'
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

from models import Spieler, Spiel, SpielZustand

# Die Trumpffarbe für das Spiel wird einmal festgelegt
trumpf = random.choice(['C', 'D', 'H', 'S'])  # Kreuz, Karo, Herz, Pik

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/spielfeld')
def spielfeld():
    print('Spielfeld Route aufgerufen')
    if 'user_id' not in session:
        print('Benutzer nicht eingeloggt, Weiterleitung zur Login-Seite')
        return redirect(url_for('login'))
    print('Benutzer eingeloggt, Rendern der Spielfeldseite')
    return render_template('spielfeld.html')


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

@socketio.on('connect')
def handle_connect():
    print('Client verbunden')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client getrennt')

@socketio.on('start_game')
def start_game(data):
    print('Spiel starten mit Daten:', data)
    try:
        spieler_anzahl = int(data.get('spieler', 2))  # Konvertiere in Integer
    except ValueError:
        print("Ungültige Anzahl von Spielern, Standardwert 2 wird verwendet.")
        spieler_anzahl = 2

    spielsitzung_id = str(uuid.uuid4())
    session['spielsitzung_id'] = spielsitzung_id

    spiel = Spiel(name="Durak Spiel", startzeit=datetime.now())
    db.session.add(spiel)

    # Karten initialisieren und mischen
    karten = ['6C', '6D', '6H', '6S', '7C', '7D', '7H', '7S', '8C', '8D', '8H', '8S', '9C', '9D', '9H', '9S', '10C', '10D', '10H', '10S', 'JC', 'JD', 'JH', 'JS', 'QC', 'QD', 'QH', 'QS', 'KC', 'KD', 'KH', 'KS', 'AC', 'AD', 'AH', 'AS']
    random.shuffle(karten)
    spieler_haende = {}
    karten_pro_spieler = 6
    for i in range(spieler_anzahl):
        spieler_haende[f"spieler_{i+1}"] = karten[i * karten_pro_spieler:(i + 1) * karten_pro_spieler]
    zieh_stapel = karten[spieler_anzahl * karten_pro_spieler:]

    aktiver_spieler_id = f"spieler_{random.randint(1, spieler_anzahl)}"

    spiel_zustand = SpielZustand(
        spielsitzung_id=spielsitzung_id,
        spieler_haende=json.dumps(spieler_haende),
        aktueller_spieler_id=aktiver_spieler_id,
        ablage_stapel=json.dumps([]),
        zieh_stapel=json.dumps(zieh_stapel)
    )
    db.session.add(spiel_zustand)
    db.session.commit()

    emit('game_started', {
        'spielsitzung_id': spielsitzung_id,
        'spieler_haende': spieler_haende,
        'aktueller_spieler': aktiver_spieler_id,
        'trumpf': trumpf
    }, room=request.sid)

@socketio.on('play_card')
def play_card(data):
    spielsitzung_id = data.get('spielsitzung_id')
    spieler_id = data.get('spieler_id')
    karte = data.get('karte')

    spiel_zustand = SpielZustand.query.filter_by(spielsitzung_id=spielsitzung_id).first()
    if not spiel_zustand:
        emit('session_not_found', {'spielsitzung_id': spielsitzung_id}, room=request.sid)
        return

    spieler_haende = json.loads(spiel_zustand.spieler_haende)
    ablage_stapel = json.loads(spiel_zustand.ablage_stapel or '[]')

    if karte in spieler_haende[spieler_id]:
        if is_valid_play(karte, ablage_stapel):
            spieler_haende[spieler_id].remove(karte)
            ablage_stapel.append(karte)
            spiel_zustand.spieler_haende = json.dumps(spieler_haende)
            spiel_zustand.ablage_stapel = json.dumps(ablage_stapel)
            
            # Überprüfe, ob ein Spieler keine Karten mehr hat (Spielende)
            if not spieler_haende[spieler_id] and not zieh_stapel:
                emit('game_over', {'message': f'Spieler {spieler_id} hat gewonnen!'}, broadcast=True)
                return

            db.session.commit()

            emit('card_played', {
                'spieler_haende': spieler_haende,
                'aktueller_spieler_id': spiel_zustand.aktueller_spieler_id,
                'ablage_stapel': ablage_stapel,
                'trumpf': trumpf
            }, room=request.sid)
        else:
            emit('invalid_play', {'message': 'Ungültiger Zug'}, room=request.sid)
    else:
        emit('invalid_play', {'message': 'Karte nicht im Besitz'}, room=request.sid)

def beende_aktiven_zug(spielsitzung_id, erfolgreicher_angriff):
    spiel_zustand = SpielZustand.query.filter_by(spielsitzung_id=spielsitzung_id).first()
    if not spiel_zustand:
        return

    spieler_haende = json.loads(spiel_zustand.spieler_haende)
    ablage_stapel = json.loads(spiel_zustand.ablage_stapel or '[]')
    zieh_stapel = json.loads(spiel_zustand.zieh_stapel or '[]')
    aktueller_spieler_id = spiel_zustand.aktueller_spieler_id

    if erfolgreicher_angriff:
        ablage_stapel = []
    else:
        spieler_haende[aktueller_spieler_id].extend(ablage_stapel)
        ablage_stapel = []

    # Ziehe Karten auf 6
    for spieler_id in spieler_haende.keys():
        while len(spieler_haende[spieler_id]) < 6 and zieh_stapel:
            spieler_haende, zieh_stapel = ziehe_karte(spieler_id, zieh_stapel, spieler_haende)

    spiel_zustand.spieler_haende = json.dumps(spieler_haende)
    spiel_zustand.ablage_stapel = json.dumps(ablage_stapel)
    spiel_zustand.zieh_stapel = json.dumps(zieh_stapel)
    spiel_zustand.aktueller_spieler_id = get_next_player(aktueller_spieler_id, list(spieler_haende.keys()))

    db.session.commit()

    emit('game_state_updated', {
        'spieler_haende': spieler_haende,
        'aktueller_spieler_id': spiel_zustand.aktueller_spieler_id,
        'ablage_stapel': ablage_stapel,
        'trumpf': trumpf
    }, broadcast=True)

@socketio.on('end_turn')
def end_turn(data):
    spielsitzung_id = data.get('spielsitzung_id')
    erfolgreicher_angriff = data.get('erfolgreicher_angriff', False)
    beende_aktiven_zug(spielsitzung_id, erfolgreicher_angriff)


def is_valid_play(karte, ablage_stapel):
    if not ablage_stapel:
        return True  # Erster Zug, keine Einschränkungen

    letzte_karte = ablage_stapel[-1]
    karte_farbe, karte_wert = karte[-1], karte[:-1]
    letzte_karte_farbe, letzte_karte_wert = letzte_karte[-1], letzte_karte[:-1]

    werte_rangfolge = ['6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

    if karte_farbe == letzte_karte_farbe:
        return werte_rangfolge.index(karte_wert) > werte_rangfolge.index(letzte_karte_wert)
    if karte_farbe == trumpf and letzte_karte_farbe != trumpf:
        return True
    return False

def get_next_player(current_player_id, player_ids):
    current_index = player_ids.index(current_player_id)
    return player_ids[(current_index + 1) % len(player_ids)]

def ziehe_karte(spieler_id, zieh_stapel, spieler_haende):
    if zieh_stapel:
        gezogene_karte = zieh_stapel.pop()
        spieler_haende[spieler_id].append(gezogene_karte)
    return spieler_haende, zieh_stapel



@socketio.on('draw_card')
def draw_card(data):
    spielsitzung_id = data.get('spielsitzung_id')
    spieler_id = data.get('spieler_id')

    spiel_zustand = SpielZustand.query.filter_by(spielsitzung_id=spielsitzung_id).first()
    if not spiel_zustand:
        emit('session_not_found', {'spielsitzung_id': spielsitzung_id}, room=request.sid)
        return

    zieh_stapel = json.loads(spiel_zustand.zieh_stapel or '[]')
    spieler_haende = json.loads(spiel_zustand.spieler_haende)

    if zieh_stapel:
        gezogene_karte = zieh_stapel.pop()
        spieler_haende[spieler_id].append(gezogene_karte)
        spiel_zustand.spieler_haende = json.dumps(spieler_haende)
        spiel_zustand.zieh_stapel = json.dumps(zieh_stapel)
        db.session.commit()

        emit('card_drawn', {
            'spieler_haende': spieler_haende,
            'zieh_stapel': zieh_stapel
        }, room=request.sid)
    else:
        emit('empty_deck', {'message': 'Keine Karten mehr im Ziehstapel!'}, room=request.sid)



if __name__ == '__main__':
    socketio.run(app, debug=True)
