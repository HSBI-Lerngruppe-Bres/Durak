// index.js

document.addEventListener('DOMContentLoaded', function () {
    const startGameButtons = document.querySelectorAll('.start-game-btn');
    startGameButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            const spielerAnzahl = this.getAttribute('data-spieler');
            startGame(spielerAnzahl);
        });
    });

    function startGame(spielerAnzahl) {
        console.log('Spiel mit ' + spielerAnzahl + ' Spielern starten');
        const socket = io();
        socket.emit('start_game', { spieler: parseInt(spielerAnzahl) });
        socket.on('game_started', function(data) {
            console.log('Spiel gestartet:', data);

            // Speichere die Daten im localStorage, um sie in spielfeld.js zu verwenden
            localStorage.setItem('game_data', JSON.stringify(data));

            window.location.href = `/spielfeld`;
        });
    }
});
