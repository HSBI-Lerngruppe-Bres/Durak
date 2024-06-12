// spielfeld.js
// Define the playCard function
const playCard = (rank, suit) => {
  socketio.emit('play_card', { rank, suit });
};

// Existing code to add event listeners
var socketio = io();

document.addEventListener('DOMContentLoaded', (event) => {
  if (!sessionStorage.getItem('joined')) {
    socketio.emit('join', {});
    sessionStorage.setItem('joined', 'true');
  }
  
  document.getElementById('start-game-btn').addEventListener("click", function() {
    socketio.emit('start_game');
  });

  document.getElementById('end-attack-btn').addEventListener("click", function() {
    socketio.emit('end_attack');
  });

  document.getElementById('take-cards-btn').addEventListener("click", function() {
    socketio.emit('take_cards');
  });
});

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

  playedCards.forEach(cardGroup => {
    const baseCard = cardGroup[0];
    const baseCardDiv = document.createElement('div');
    baseCardDiv.className = 'card';
    baseCardDiv.setAttribute('data-rank', baseCard.rank);
    baseCardDiv.setAttribute('data-suit', baseCard.suit);
    baseCardDiv.setAttribute('draggable', 'true');
    baseCardDiv.addEventListener('dragstart', handleDragStart);
    baseCardDiv.addEventListener('dragend', handleDragEnd);
    baseCardDiv.addEventListener('dragover', handleDragOver);
    baseCardDiv.addEventListener('dragleave', handleDragLeave);
    baseCardDiv.addEventListener('drop', handleDrop);
    const img = document.createElement('img');
    img.src = `/static/svg/${baseCard.rank}${baseCard.suit}.svg`;
    img.alt = `${baseCard.rank} of ${baseCard.suit}`;
    baseCardDiv.appendChild(img);

    cardGroup.slice(1).forEach(overlaidCard => {
      const overlayCardDiv = document.createElement('div');
      overlayCardDiv.className = 'card card-overlay';
      overlayCardDiv.setAttribute('data-rank', overlaidCard.rank);
      overlayCardDiv.setAttribute('data-suit', overlaidCard.suit);
      overlayCardDiv.setAttribute('draggable', 'true');
      overlayCardDiv.addEventListener('dragstart', handleDragStart);
      overlayCardDiv.addEventListener('dragend', handleDragEnd);
      overlayCardDiv.addEventListener('dragover', handleDragOver);
      overlayCardDiv.addEventListener('dragleave', handleDragLeave);
      overlayCardDiv.addEventListener('drop', handleDrop);
      const overlayImg = document.createElement('img');
      overlayImg.src = `/static/svg/${overlaidCard.rank}${overlaidCard.suit}.svg`;
      overlayImg.alt = `${overlaidCard.rank} of ${overlaidCard.suit}`;
      overlayCardDiv.appendChild(overlayImg);

      baseCardDiv.style.position = 'relative';
      overlayCardDiv.style.position = 'absolute';
      overlayCardDiv.style.top = '0';
      overlayCardDiv.style.left = '0';
      overlayCardDiv.style.zIndex = '10';

      baseCardDiv.appendChild(overlayCardDiv);
    });

    playedCardsDiv.appendChild(baseCardDiv);
  });
});

// Update the current player
socketio.on('update_current_player', (data) => {
  const currentPlayer = data.current_player;
  createMessage('System', `Der aktuelle Spieler ist nun ${currentPlayer}.`);
});

// Clear played cards
socketio.on('clear_played_cards', () => {
  const playedCardsDiv = document.getElementById('played-cards');
  playedCardsDiv.innerHTML = '';
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

// Neuer Event-Listener für die überlagerte Karte
socketio.on('card_overplayed', (data) => {
  const { rank, suit, target_index } = data;
  const playedCardsDiv = document.getElementById('played-cards');
  const targetElement = playedCardsDiv.children[target_index];

  // Überlagerte Karte erstellen
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

  // Positionieren der überlagerten Karte
  targetElement.style.position = 'relative';
  cardDiv.style.position = 'absolute';
  cardDiv.style.top = '0';
  cardDiv.style.left = '0';
  cardDiv.style.zIndex = '10';

  targetElement.appendChild(cardDiv);
});

// Drag and Drop Handler Functions
const handleDragStart = (event) => {
  let element = event.target;
  if (element.tagName === 'IMG') {
      element = element.parentElement; // Get the button element if the target is the image
  }
  const rank = element.dataset.rank;
  const suit = element.dataset.suit;
  console.log(`Drag Start: Rank: ${rank}, Suit: ${suit}`);
  event.dataTransfer.setData('text/plain', `${rank}-${suit}`);
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
      const rank = element.dataset.rank;
      const suit = element.dataset.suit
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
        const rank = element.dataset.rank;
        const suit = element.dataset.suit;
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
        const rank = element.dataset.rank;
        const suit = element.dataset.suit;
        console.log(`Drag Leave: Rank: ${rank}, Suit: ${suit}`);
    }
  };
  
  const handleDrop = (event) => {
    event.preventDefault();
    const data = event.dataTransfer.getData('text/plain');
    const [draggedRank, draggedSuit] = data.split('-');
    console.log(`Drop: Rank: ${draggedRank}, Suit: ${draggedSuit}`);
    
    let element = event.target;
    if (element.tagName === 'IMG') {
        element = element.parentElement; // Get the button element if the target is the image
    }
    if (element.classList.contains('card-button') || element.classList.contains('card')) {
        element.classList.remove('highlight');
        
        // Zielkarteninformationen extrahieren
        const targetRank = element.dataset.rank;
        const targetSuit = element.dataset.suit;
        
        console.log(`Karte ${draggedRank}${draggedSuit} wurde auf ${targetRank}${targetSuit} gelegt`);
        
        // Überprüfen, ob die Karte aus der Hand des Spielers stammt
        const deckDiv = document.getElementById('deck');
        const isFromHand = Array.from(deckDiv.children).some(card => card.dataset.rank === draggedRank && card.dataset.suit === draggedSuit);
  
        if (isFromHand) {
            // Überlagerungskarte an den Server senden
            socketio.emit('overplay_card', { rank: draggedRank, suit: draggedSuit, target_index: [...element.parentElement.children].indexOf(element) });
        } else {
            console.log('Die Karte stammt nicht aus der Hand des Spielers und kann nicht erneut verwendet werden.');
        }
    } else {
        console.log('Drop-Ziel ist keine Karte');
    }
  };
  
  // Event-Listener hinzufügen
  const addEventListeners = () => {
    const cards = document.querySelectorAll('.card-button, .card');
    cards.forEach(card => {
        card.addEventListener('dragstart', handleDragStart);
        card.addEventListener('dragend', handleDragEnd);
        card.addEventListener('dragenter', handleDragEnter);
        card.addEventListener('dragover', handleDragOver);
        card.addEventListener('dragleave', handleDragLeave);
        card.addEventListener('drop', handleDrop);
    });
  };
  
  // Initialisieren Sie die Drop-Ziele beim Laden der Seite
  document.querySelectorAll('#played-cards .card').forEach(card => {
    card.addEventListener('dragenter', handleDragEnter);
    card.addEventListener('dragover', handleDragOver);
    card.addEventListener('dragleave', handleDragLeave);
    card.addEventListener('drop', handleDrop);
  });

// Neuer Event-Listener für das Spielende
socketio.on('game_over', (data) => {
  const placements = data.placements;
  let message = 'Spiel beendet! Platzierungen:\n';
  for (const [player, place] of Object.entries(placements)) {
    message += `${player}: ${place}\n`;
  }
  alert(message);
});

