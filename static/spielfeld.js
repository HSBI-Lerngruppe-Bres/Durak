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
    const cardDiv = document.createElement('button');
    cardDiv.className = 'card-button';
    cardDiv.setAttribute('data-rank', card.rank);
    cardDiv.setAttribute('data-suit', card.suit);
    cardDiv.setAttribute('draggable', 'true');
    cardDiv.addEventListener('click', () => playCard(card.rank, card.suit));
    cardDiv.addEventListener('dragstart', handleDragStart);
    cardDiv.addEventListener('dragend', handleDragEnd);
    const img = document.createElement('img');
    img.src = `/static/svg/${card.rank}${card.suit}.svg`;
    img.alt = `${card.rank} of ${card.suit}`;
    cardDiv.appendChild(img);
    deckDiv.appendChild(cardDiv);
  });
});
/*
const playCard = (rank, suit) => {
  socketio.emit('play_card', { rank, suit });
};
*/
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
  cardDiv.setAttribute('data-rank', rank);
  cardDiv.setAttribute('data-suit', suit);
  cardDiv.setAttribute('draggable', 'true');
  cardDiv.addEventListener('dragstart', handleDragStart);
  cardDiv.addEventListener('dragend', handleDragEnd);
  cardDiv.addEventListener('dragover', handleDragOver);
  cardDiv.addEventListener('dragleave', handleDragLeave);
  cardDiv.addEventListener('drop', handleDrop);
  const img = document.createElement('img');
  img.src = `/static/svg/${rank}${suit}.svg`;
  img.alt = `${rank} of ${suit}`;
  cardDiv.appendChild(img);
  playedCardsDiv.appendChild(cardDiv);
});

socketio.on('update_played_cards', (data) => {
  const playedCards = data.played_cards;
  const playedCardsDiv = document.getElementById('played-cards');
  playedCardsDiv.innerHTML = '';
  playedCards.forEach(card => {
    const cardDiv = document.createElement('div');
    cardDiv.className = 'card';
    cardDiv.setAttribute('data-rank', card.rank);
    cardDiv.setAttribute('data-suit', card.suit);
    cardDiv.setAttribute('draggable', 'true');
    cardDiv.addEventListener('dragstart', handleDragStart);
    cardDiv.addEventListener('dragend', handleDragEnd);
    cardDiv.addEventListener('dragover', handleDragOver);
    cardDiv.addEventListener('dragleave', handleDragLeave);
    cardDiv.addEventListener('drop', handleDrop);
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
  deckDiv.innerHTML = '';
  hand.forEach(card => {
    const cardDiv = document.createElement('button');
    cardDiv.className = 'card-button';
    cardDiv.setAttribute('draggable', 'true');
    cardDiv.setAttribute('data-rank', card.rank);
    cardDiv.setAttribute('data-suit', card.suit);
    cardDiv.addEventListener('click', () => playCard(card.rank, card.suit));
    cardDiv.addEventListener('dragstart', handleDragStart);
    cardDiv.addEventListener('dragend', handleDragEnd);
    cardDiv.addEventListener('dragover', handleDragOver);
    cardDiv.addEventListener('dragleave', handleDragLeave);
    cardDiv.addEventListener('drop', handleDrop);
    const img = document.createElement('img');
    img.src = `/static/svg/${card.rank}${card.suit}.svg`;
    img.alt = `${card.rank} of ${card.suit}`;
    cardDiv.appendChild(img);
    deckDiv.appendChild(cardDiv);
  });
});


// Drag and Drop Handler Functions
const handleDragStart = (event) => {
    let element = event.target;
    if (element.tagName === 'IMG') {
        element = element.parentElement; // Get the button element if the target is the image
    }
    const rank = element.dataset.rank || 'undefined';
    const suit = element.dataset.suit || 'undefined';
    console.log(`Drag Start: Rank: ${rank}, Suit: ${suit}`);
    event.dataTransfer.setData('text/plain', `${rank}${suit}`);
    element.classList.add('dragging');
};

const handleDragEnd = (event) => {
    document.querySelectorAll('.highlight').forEach(el => el.classList.remove('highlight'));
    let element = event.target;
    if (element.tagName === 'IMG') {
        element = element.parentElement; // Get the button element if the target is the image
    }
    element.classList.remove('dragging');
    console.log('Drag End');
};

const handleDragEnter = (event) => {
    let element = event.target;
    if (element.tagName === 'IMG') {
        element = element.parentElement; // Get the button element if the target is the image
    }
    if (element.classList.contains('card-button') || element.classList.contains('card')) {
        element.classList.add('highlight');
        const rank = element.dataset.rank || 'undefined';
        const suit = element.dataset.suit || 'undefined';
        console.log(`Drag Enter: Rank: ${rank}, Suit: ${suit}`);
    }
};

const handleDragOver = (event) => {
    event.preventDefault();
    let element = event.target;
    if (element.tagName === 'IMG') {
        element = element.parentElement; // Get the button element if the target is the image
    }
    if (element.classList.contains('card-button') || element.classList.contains('card')) {
        const rank = element.dataset.rank || 'undefined';
        const suit = element.dataset.suit || 'undefined';
        console.log(`Drag Over: Rank: ${rank}, Suit: ${suit}`);
    }
};

const handleDragLeave = (event) => {
    let element = event.target;
    if (element.tagName === 'IMG') {
        element = element.parentElement; // Get the button element if the target is the image
    }
    if (element.classList.contains('card-button') || element.classList.contains('card')) {
        element.classList.remove('highlight');
        const rank = element.dataset.rank || 'undefined';
        const suit = element.dataset.suit || 'undefined';
        console.log(`Drag Leave: Rank: ${rank}, Suit: ${suit}`);
    }
};

const handleDrop = (event) => {
    event.preventDefault();
    const data = event.dataTransfer.getData('text/plain');
    const draggedRank = data.slice(0, -1) || 'undefined';
    const draggedSuit = data.slice(-1) || 'undefined';
    console.log(`Drop: Rank: ${draggedRank}, Suit: ${draggedSuit}`);
    
    let element = event.target;
    if (element.tagName === 'IMG') {
        element = element.parentElement; // Get the button element if the target is the image
    }
    if (element.classList.contains('card-button') || element.classList.contains('card')) {
        element.classList.remove('highlight');
        
        // Zielkarteninformationen extrahieren
        const targetRank = element.dataset.rank || 'undefined';
        const targetSuit = element.dataset.suit || 'undefined';
        
        console.log(`Karte ${draggedRank}${draggedSuit} wurde auf ${targetRank}${targetSuit} gelegt`);
        
        // Aufrufen der overlayCard Funktion
        overlayCard(draggedRank, draggedSuit, element);
    } else {
        console.log('Drop-Ziel ist keine Karte');
    }
};

const overlayCard = (rank, suit, targetElement) => {
  console.log(`Karte überlagert: ${rank}${suit} auf ${targetElement.dataset.rank}${targetElement.dataset.suit}`);
  
  // Erstellen Sie die überlagerte Karte
  const cardDiv = document.createElement('div');
  cardDiv.className = 'card card-overlay';
  cardDiv.setAttribute('data-rank', rank);
  cardDiv.setAttribute('data-suit', suit);
  cardDiv.setAttribute('draggable', 'true');
  cardDiv.addEventListener('dragstart', handleDragStart);
  cardDiv.addEventListener('dragend', handleDragEnd);
  cardDiv.addEventListener('dragover', handleDragOver);
  cardDiv.addEventListener('dragleave', handleDragLeave);
  cardDiv.addEventListener('drop', handleDrop);

  const img = document.createElement('img');
  img.src = `/static/svg/${rank}${suit}.svg`;
  img.alt = `${rank} of ${suit}`;
  cardDiv.appendChild(img);

  // Positionieren Sie die überlagerte Karte
  targetElement.style.position = 'relative';
  cardDiv.style.position = 'absolute';
  cardDiv.style.top = '0';
  cardDiv.style.left = '0';
  cardDiv.style.zIndex = '10';
  
  targetElement.appendChild(cardDiv);
  
  socketio.emit('overplay_card', { rank, suit });
};

const playCard = (rank, suit) => {
    console.log(`Karte gespielt: ${rank}${suit}`);
    socketio.emit('play_card', { rank, suit });
};

// Event-Listener hinzufügen
const addEventListeners = () => {
    const cards = document.querySelectorAll('.card-button, .card');
    console.log('Karten gefunden:', cards.length); // Überprüfen Sie, ob Karten gefunden werden
    cards.forEach(card => {
        const rank = card.dataset.rank || 'undefined';
        const suit = card.dataset.suit || 'undefined';
        console.log(`Karte gefunden: Rank: ${rank}, Suit: ${suit}`);
        card.addEventListener('dragstart', handleDragStart);
        card.addEventListener('dragend', handleDragEnd);
        card.addEventListener('dragenter', handleDragEnter);
        card.addEventListener('dragover', handleDragOver);
        card.addEventListener('dragleave', handleDragLeave);
        card.addEventListener('drop', handleDrop);
        console.log('Event-Listener für Karte hinzugefügt:', card);
    });
    console.log('Event-Listener hinzugefügt');
};

// Initialisieren Sie die Drop-Ziele beim Laden der Seite
document.querySelectorAll('#played-cards .card').forEach(card => {
    addDropListeners(card);
    console.log('Drop-Listener für gespielte Karten hinzugefügt', card);
});
