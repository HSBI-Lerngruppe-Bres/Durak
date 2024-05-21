import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
from database import db
from flask_migrate import Migrate
import random
import json
from datetime import datetime
import uuid
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

@app.route('/static/svg/<path:filename>')
def custom_static(filename):
    return send_from_directory(os.path.join(app.root_path, 'static/svg'), filename)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/spielfeld')
def spielfeld():
    if 'user_id' not in session:
        return redirect(url_for('login'))
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
    spieler_anzahl = data.get('spieler', 2)  # Default-Wert auf 2 setzen, falls nichts übergeben wurde

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

    # Bestimme den Trumpf
    trumpf_karte = zieh_stapel.pop()
    trumpf = trumpf_karte[-1]
    zieh_stapel.append(trumpf_karte)

    aktiver_spieler_id = f"spieler_{random.randint(1, spieler_anzahl)}"

    spiel_zustand = SpielZustand(
        spielsitzung_id=spielsitzung_id,
        spieler_haende=json.dumps(spieler_haende),
        aktueller_spieler_id=aktiver_spieler_id,
        ablage_stapel=json.dumps([]),  # Leeres Array, um 'NOT NULL' Constraint zu erfüllen
        zieh_stapel=json.dumps(zieh_stapel),
        trumpf=trumpf  # Trumpf initialisieren
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
    aktueller_spieler = spiel_zustand.aktueller_spieler_id
    trumpf = spiel_zustand.trumpf

    if karte in spieler_haende[spieler_id] and spieler_id == aktueller_spieler:
        if len(ablage_stapel) % 2 == 0:  # Attack phase
            if is_valid_attack(karte, ablage_stapel):
                spieler_haende[spieler_id].remove(karte)
                ablage_stapel.append(karte)
            else:
                emit('invalid_play', {'message': 'Invalid attack'}, room=request.sid)
                return
        else:  # Defense phase
            if is_valid_defense(ablage_stapel[-1], karte, trumpf):
                spieler_haende[spieler_id].remove(karte)
                ablage_stapel.append(karte)
            else:
                emit('invalid_play', {'message': 'Invalid defense'}, room=request.sid)
                return

        spiel_zustand.spieler_haende = json.dumps(spieler_haende)
        spiel_zustand.ablage_stapel = json.dumps(ablage_stapel)
        
        if not spieler_haende[spieler_id] and not json.loads(spiel_zustand.zieh_stapel):
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
        emit('invalid_play', {'message': 'Not your turn'}, room=request.sid)

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
    for spieler_id in spieler_haende.keys():
        while len(spieler_haende[spieler_id]) < 6 and zieh_stapel:
            spieler_haende, zieh_stapel = ziehe_karte(spieler_id, zieh_stapel, spieler_haende)
    spiel_zustand.spieler_haende = json.dumps(spieler_haende)
    spiel_zustand.ablage_stapel = json.dumps(ablage_stapel)
    spiel_zustand.zieh_stapel = json.dumps(zieh_stapel)
    spiel_zustand.aktueller_spieler_id = get_next_player(aktueller_spieler_id, list(spieler_haende.keys()), erfolgreicher_angriff)
    db.session.commit()
    emit('game_state_updated', {
        'spieler_haende': spieler_haende,
        'aktueller_spieler_id': spiel_zustand.aktueller_spieler_id,
        'ablage_stapel': ablage_stapel,
        'trumpf': spiel_zustand.trumpf
    }, broadcast=True)


@socketio.on('end_turn')
def end_turn(data):
    spielsitzung_id = data.get('spielsitzung_id')
    erfolgreicher_angriff = data.get('erfolgreicher_angriff', False)
    beende_aktiven_zug(spielsitzung_id, erfolgreicher_angriff)


def is_valid_play(karte, ablage_stapel, trumpf):
    if not ablage_stapel:
        return True  # Erster Zug, keine Einschränkungen

    letzte_karte = ablage_stapel[-1]
    karte_farbe, karte_wert = karte[-1], karte[:-1]
    letzte_karte_farbe, letzte_karte_wert = letzte_karte[-1], letzte_karte[:-1]

    werte_rangfolge = ['6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

    if len(ablage_stapel) % 2 == 0:  # Angriffsphase
        return all(k[:-1] == karte[:-1] for k in ablage_stapel)  # Karten müssen denselben Wert haben
    else:  # Verteidigungsphase
        return is_valid_defense(letzte_karte, karte, trumpf)


def get_next_player(current_player, players, erfolgreicher_angriff):
    current_index = players.index(current_player)
    return players[(current_index + 1) % len(players)] if erfolgreicher_angriff else players[(current_index + 1) % len(players)]


def ziehe_karte(spieler_id, zieh_stapel, spieler_haende):
    if zieh_stapel:
        karte = zieh_stapel.pop(0)
        spieler_haende[spieler_id].append(karte)
    return spieler_haende, zieh_stapel

def is_valid_attack(karte, ablage_stapel):
    if not ablage_stapel:
        return True  # First attack, no restrictions

    karte_wert = karte[:-1]
    return all(k[:-1] == karte_wert for k in ablage_stapel if k != 'back')

def is_valid_defense(angriffskarte, verteidigungskarte, trumpf):
    ang_farbe, ang_wert = angriffskarte[-1], angriffskarte[:-1]
    vert_farbe, vert_wert = verteidigungskarte[-1], verteidigungskarte[:-1]

    werte_rangfolge = ['6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

    if vert_farbe == ang_farbe:
        return werte_rangfolge.index(vert_wert) > werte_rangfolge.index(ang_wert)
    if vert_farbe == trumpf and ang_farbe != trumpf:
        return True
    return False


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
