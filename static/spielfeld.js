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

socketio.on("update_deck", (data) => {
  const deck = data.deck;
  const deckDiv = document.getElementById("deck");
  deckDiv.innerHTML = '';
  deck.forEach(card => {
    const cardDiv = document.createElement('div');
    cardDiv.className = 'card';
    const img = document.createElement('img');
    img.src = `/static/svg/${card.rank}${card.suit}.svg`;
    img.alt = `${card.rank} of ${card.suit}`;
    cardDiv.appendChild(img);
    deckDiv.appendChild(cardDiv);
  });
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
