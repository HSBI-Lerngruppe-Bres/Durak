// spielfeld.js
var socketio = io();

const messages = document.getElementById("messages");

const createMessage = (name, msg) => {
  const content = `
  <div class="text">
      <span>
          <strong>${name}</strong>: ${msg}
      </span>
      <span class="muted">
          ${new Date().toLocaleString()}
      </span>
  </div>
  `;
  messages.innerHTML += content;
};

socketio.on("message", (data) => {
  createMessage(data.name, data.message);
});

document.getElementById('copy-btn').addEventListener("click", function() {
  const textarea = document.getElementById('code-textarea');
  textarea.select();
  textarea.setSelectionRange(0, 99999); // Für mobile Geräte

  try {
      const successful = document.execCommand('copy');
      if (successful) {
          alert('Text wurde in die Zwischenablage kopiert.');
      } else {
          throw new Error('Kopiervorgang nicht erfolgreich.');
      }
  } catch (err) {
      alert('Fehler beim Kopieren des Textes: ' + err);
  }
});

socketio.on("update_deck", (data) => {
  const deck = data.deck;
  const deckDiv = document.getElementById("deck");
  deckDiv.innerHTML = '';
  deck.forEach(card => {
    const cardDiv = document.createElement('div');
    cardDiv.className = 'card';
    cardDiv.setAttribute('data-rank', card.rank);
    cardDiv.setAttribute('data-suit', card.suit);
    cardDiv.addEventListener('click', () => playCard(card.rank, card.suit)); // Click event to play the card
    const img = document.createElement('img');
    img.src = `/static/svg/${card.rank}${card.suit}.svg`;
    img.alt = `${card.rank} of ${card.suit}`;
    cardDiv.appendChild(img);
    deckDiv.appendChild(cardDiv);
  });
});

const playCard = (rank, suit) => {
  socketio.emit('play_card', { rank, suit });
};

document.getElementById('start-game-btn').addEventListener("click", function() {
  socketio.emit('start_game');
});

socketio.on('redirect', (data) => {
  window.location.href = data.url + "?error=The game has already started, please choose another Gameroom or create a new one.";
});

socketio.on('start_player', (data) => {
  const startPlayer = data.player;
  createMessage('System', `${startPlayer} beginnt das Spiel.`);
});

socketio.on('card_played', (data) => {
  const { rank, suit, player } = data;
  createMessage('System', `${player} hat die Karte ${rank} of ${suit} gespielt.`);
  const playedCardsDiv = document.getElementById('played-cards');
  const cardDiv = document.createElement('div');
  cardDiv.className = 'card';
  const img = document.createElement('img');
  img.src = `/static/svg/${rank}${suit}.svg`;
  img.alt = `${rank} of ${suit}`;
  cardDiv.appendChild(img);
  playedCardsDiv.appendChild(cardDiv);
});

socketio.on('update_played_cards', (data) => {
  const playedCards = data.played_cards;
  const playedCardsDiv = document.getElementById('played-cards');
  playedCardsDiv.innerHTML = ''; // Clear the div first
  playedCards.forEach(card => {
    const cardDiv = document.createElement('div');
    cardDiv.className = 'card';
    const img = document.createElement('img');
    img.src = `/static/svg/${card.rank}${card.suit}.svg`;
    img.alt = `${card.rank} of ${card.suit}`;
    cardDiv.appendChild(img);
    playedCardsDiv.appendChild(cardDiv);
  });
});

// Neuer Event-Listener für die Aktualisierung der Hand des Spielers
socketio.on('update_hand', (data) => {
  const hand = data.hand;
  const deckDiv = document.getElementById('deck');
  deckDiv.innerHTML = ''; // Clear the div first
  hand.forEach(card => {
    const cardDiv = document.createElement('div');
    cardDiv.className = 'card';
    cardDiv.setAttribute('data-rank', card.rank);
    cardDiv.setAttribute('data-suit', card.suit);
    cardDiv.addEventListener('click', () => playCard(card.rank, card.suit)); // Click event to play the card
    const img = document.createElement('img');
    img.src = `/static/svg/${card.rank}${card.suit}.svg`;
    img.alt = `${card.rank} of ${card.suit}`;
    cardDiv.appendChild(img);
    deckDiv.appendChild(cardDiv);
  });
});
