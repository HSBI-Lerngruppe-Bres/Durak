// register.js

document.addEventListener('DOMContentLoaded', function() {
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', function(event) {
            event.preventDefault();
            const name = document.getElementById('name').value;
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            // Hier könnten Sie weitere Validierung einfügen
            
            // Annehmen, dass eine Funktion register existiert, um den Benutzer zu registrieren
            register(name, email, password);
        });
    }
});

function register(name, email, password) {
    // Annehmen, dass Sie Ajax verwenden, um sich zu registrieren
    console.log('Register attempt with:', name, email, password);
    // Weiter Logik für den Registrierungsprozess
}
