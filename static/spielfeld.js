document.addEventListener('DOMContentLoaded', function () {
    var socket = io();
    console.log('Socket initialized:', socket);

    socket.on('connect', () => {
        console.log('Connected to server');
        socket.emit('join_game');
    });

    socket.on('connect_error', (err) => {
        console.error('Connection error:', err);
    });

    socket.on('disconnect', (reason) => {
        console.warn('Disconnected from server:', reason);
    });

    socket.on('game_started', function (data) {
        console.log('Game started:', data);
        window.localStorage.setItem('spielsitzung_id', data.spielsitzung_id);
        updateGameView(data);
    });

    socket.on('game_state_updated', function (data) {
        console.log('Received game state data:', data);
        updateGameView(data);
    });

    socket.on('invalid_play', function (data) {
        alert(data.message);
    });

    socket.on('game_over', function (data) {
        alert(data.message);
        // Optionally reset the game or redirect the user
    });

    document.getElementById('end-turn-btn').addEventListener('click', function () {
        const spielsitzung_id = window.localStorage.getItem('spielsitzung_id');
        const aktueller_spieler = document.querySelector('.active').id.includes('player1') ? 'spieler_1' : 'spieler_2';
        const erfolgreicher_angriff = confirm("War der Angriff erfolgreich?");
        socket.emit('end_turn', { spielsitzung_id: spielsitzung_id, erfolgreicher_angriff: erfolgreicher_angriff });
    });

    function updateGameView(data) {
        console.log('Updating game view with data:', data);
        if (!data.spieler_haende) {
            console.error('Missing card data in received game state:', data);
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
            console.error('Missing cards for player 1');
        }

        if (data.spieler_haende.spieler_2) {
            updateHandView(player2Hand, data.spieler_haende.spieler_2, 'spieler_2');
        } else {
            console.error('Missing cards for player 2');
        }

        updateHandView(discardPile, data.ablage_stapel || []);

        // Show the trump symbol
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

        // Show the backside of the draw pile only if the pile is not empty
        if (data.zieh_stapel && data.zieh_stapel.length > 0) {
            const cardBackPath = drawPile.getAttribute('data-backside');
            if (cardBackPath) {
                drawPile.style.backgroundImage = `url('${cardBackPath}')`;
                drawPile.style.backgroundSize = 'cover';
                drawPile.style.display = 'block';
            } else {
                drawPile.style.display = 'none';
            }
        } else {
            drawPile.style.display = 'none';
        }

        // Highlight the current player
        if (aktuellerSpieler === 'spieler_1') {
            player1Hand.classList.add('active');
            player2Hand.classList.remove('active');
        } else {
            player1Hand.classList.remove('active');
            player2Hand.classList.add('active');
        }
    }

    function updateHandView(handElement, cards, spieler_id) {
        const cardPath = document.getElementById('game-container').getAttribute('data-card-path');
        console.log(`Card path: ${cardPath}`);  // Log the card path
        handElement.innerHTML = '';
        cards.forEach(card => {
            const cardElement = document.createElement('div');
            cardElement.className = 'card';
            const cardImagePath = `${cardPath}/${card}.svg`;
            console.log(`Card image path: ${cardImagePath}`);  // Log each card image path
            cardElement.style.backgroundImage = `url('${cardImagePath}')`;
            cardElement.addEventListener('click', () => {
                console.log(`Card played: ${card} by ${spieler_id}`);
                const spielsitzung_id = window.localStorage.getItem('spielsitzung_id');
                socket.emit('play_card', { spielsitzung_id: spielsitzung_id, spieler_id: spieler_id, karte: card });
            });
            handElement.appendChild(cardElement);
        });
    }

    function showNotification(message) {
        document.getElementById('notificationMessage').innerText = message;
        var notificationModal = new bootstrap.Modal(document.getElementById('notificationModal'));
        notificationModal.show();
    }
});
