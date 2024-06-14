document.addEventListener('DOMContentLoaded', () => {
    // Existing code...

    const copyLinkBtn = document.getElementById('copy-link-btn');
    if (copyLinkBtn) {
        copyLinkBtn.addEventListener('click', copyLink);
    }
});

function copyLink() {
    const roomCode = document.querySelector('.game-room-title').textContent.split(' ')[2];
    const link = `${window.location.origin}/room/${roomCode}`;
    navigator.clipboard.writeText(link).then(() => {
        alert('Link kopiert: ' + link);
    });
}
