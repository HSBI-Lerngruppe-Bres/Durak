// login.js

document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', function(event) {
            event.preventDefault();
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            
            // Hier könnten Sie weitere Validierung einfügen

            // Annehmen, dass eine Funktion login existiert, um den Benutzer anzumelden
            login(email, password);
        });
    }
});
function login(email, password) {
    // Annehmen, dass Sie Ajax verwenden, um sich anzumelden
    console.log('Login attempt with:', email, password);
    // Weiter Logik für den Login-Prozess
}
