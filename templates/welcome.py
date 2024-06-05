<!-- welcome.html -->
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Willkommen beim Durak Kartenspiel</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="icon" type="image/x-icon" href="{{ url_for('static', filename='favicon.ico') }}">
</head>
<body>
    <div class="container text-center">
        <h1>Willkommen beim Durak Kartenspiel</h1>
        <p>Bitte melden Sie sich an oder registrieren Sie sich, um zu spielen.</p>
        <a href="{{ url_for('login') }}" class="btn btn-primary">Anmelden</a>
        <a href="{{ url_for('register') }}" class="btn btn-secondary">Registrieren</a>
    </div>
</body>
</html>