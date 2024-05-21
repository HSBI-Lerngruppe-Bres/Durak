// spielfeld.js

document.addEventListener('DOMContentLoaded', function () {
    var socket = io();
    console.log('Socket initialisiert:', socket);

    socket.on('connect', () => {
        console.log('Verbunden mit Server');
        socket.emit('join_game'); // Bereitstellung, wenn nötig
    });

    const savedGameData = localStorage.getItem('game_data');
    if (savedGameData) {
        const data = JSON.parse(savedGameData);
        console.log('Geladene Spieldaten:', data);
        updateGameView(data);
    }

    socket.on('game_state_updated', function(data) {
        console.log('Empfangene Spielzustandsdaten:', data);
        updateGameView(data);
    });

    socket.on('invalid_play', function(data) {
        console.error('Ungültiger Zug:', data.message);
        alert(data.message);
    });

    socket.on('game_over', function(data) {
        console.log('Spiel beendet:', data.message);
        alert(data.message);
    });

    function updateGameView(data) {
        console.log('Aktualisiere Spielansicht mit Daten:', data);
        if (!data.spieler_haende) {
            console.error('Fehlende Kartendaten im empfangenen Spielzustand:', data);
            return;
        }

        const player1Hand = document.getElementById('player1-hand');
        const player2Hand = document.getElementById('player2-hand');
        const discardPile = document.getElementById('discard-pile');
        const trumpfSymbol = document.getElementById('trumpf-symbol');
        const drawPile = document.getElementById('draw-pile');
        const aktuellerSpieler = data.aktueller_spieler_id;

        if (data.spieler_haende.spieler_1) {
            updateHandView(player1Hand, data.spieler_haende.spieler_1, 'spieler_1');
        } else {
            console.error('Fehlende Karten für Spieler 1');
        }

        if (data.spieler_haende.spieler_2) {
            updateHandView(player2Hand, data.spieler_haende.spieler_2, 'spieler_2');
        } else {
            console.error('Fehlende Karten für Spieler 2');
        }

        updateHandView(discardPile, data.ablage_stapel || []);

        // Zeige das Trumpfsymbol
        const trumpf = data.trumpf;
        switch (trumpf) {
            case 'C':
                trumpfSymbol.innerHTML = '♣️';
                break;
            case 'D':
                trumpfSymbol.innerHTML = '♦️';
                break;
            case 'H':
                trumpfSymbol.innerHTML = '♥️';
                break;
            case 'S':
                trumpfSymbol.innerHTML = '♠️';
                break;
            default:
                trumpfSymbol.innerHTML = '';
        }

        // Zeige die Rückseite der Ziehkarte
        const cardBackPath = `/static/svg/2B-backside.svg`;
        drawPile.style.backgroundImage = `url('${cardBackPath}')`;
        drawPile.style.backgroundSize = 'cover';

        // Highlight aktuellen Spieler
        if (aktuellerSpieler === 'spieler_1') {
            player1Hand.classList.add('active');
            player2Hand.classList.remove('active');
        } else {
            player1Hand.classList.remove('active');
            player2Hand.classList.add('active');
        }
    }

    function updateHandView(handElement, cards, spielerId) {
        handElement.innerHTML = '';
        if (!cards) {
            console.error('Karten für Spieler', spielerId, 'sind nicht definiert');
            return;
        }

        cards.forEach(card => {
            const cardElement = document.createElement('div');
            cardElement.className = 'card';
            const cardPath = `/static/svg/${card}.svg`;
            console.log('Lade Kartenbild:', cardPath);
            cardElement.style.backgroundImage = `url('${cardPath}')`;
            cardElement.style.backgroundSize = 'cover';
            cardElement.addEventListener('click', function() {
                playCard(card, spielerId);
            });
            handElement.appendChild(cardElement);
        });
    }

    function playCard(card, spielerId) {
        console.log(`Karte gespielt: ${card} von ${spielerId}`);
        const spielsitzungId = JSON.parse(localStorage.getItem('game_data')).spielsitzung_id;
        socket.emit('play_card', { spielsitzung_id: spielsitzungId, spieler_id: spielerId, karte: card });
    }

    socket.on('card_played', function(data) {
        console.log('Karte gespielt:', data);
        updateGameView(data);
    });

    // Funktion zum Ziehen von Karten
    window.drawCard = function(spielerId) {
        const spielsitzungId = JSON.parse(localStorage.getItem('game_data')).spielsitzung_id;
        socket.emit('draw_card', { spielsitzung_id: spielsitzungId, spieler_id: spielerId });
    }

    // Funktion zum Beenden des Zugs
    window.endTurn = function(erfolgreicherAngriff) {
        const spielsitzungId = JSON.parse(localStorage.getItem('game_data')).spielsitzung_id;
        socket.emit('end_turn', { spielsitzung_id: spielsitzungId, erfolgreicher_angriff: erfolgreicherAngriff });
    }
});
