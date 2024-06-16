# Durak

![Durak Logo](static/images/261787.ico)

## Überblick

**Durak** ist ein Mehrspieler-Kartenspiel, bei dem die Spieler darum kämpfen, nicht der letzte zu sein, der noch Karten auf der Hand hat. Das Spiel wurde mit Flask, SocketIO und SQLAlchemy entwickelt und bietet Echtzeit-Interaktionen sowie eine moderne Weboberfläche.

## Funktionen

- Echtzeit-Mehrspieler-Gameplay
- Benutzerauthentifizierung und Sitzungsverwaltung
- Interaktive Benutzeroberfläche mit Echtzeit-Updates
- Plattformübergreifende Unterstützung (Windows, macOS, Linux)

## Inhaltsverzeichnis

- [Anforderungen](#anforderungen)
- [Installation](#installation)
  - [Windows](#windows)
  - [macOS](#macos)
  - [Linux](#linux)
- [Spiel starten](#spiel-starten)
- [Beitragen](#beitragen)
- [Lizenz](#lizenz)

## Anforderungen

- Python 3.9 oder höher
- Poetry zur Abhängigkeitsverwaltung

## Installation

### Windows

1. **Repository klonen:**

    ```sh
    git clone https://github.com/HSBI-Lerngruppe-Bres/Durak.git
    cd Durak
    ```

2. **Poetry installieren:**

    ```sh
    pip install --user pipx
    pipx install poetry
    ```

3. **Abhängigkeiten installieren:**

    ```sh
    poetry install
    ```

### macOS

1. **Repository klonen:**

    ```sh
    git clone https://github.com/HSBI-Lerngruppe-Bres/Durak.git
    cd Durak
    ```

2. **Poetry installieren:**

    ```sh
    brew install pipx
    pipx install poetry
    ```

3. **Abhängigkeiten installieren:**

    ```sh
    poetry install
    ```

### Linux

1. **Repository klonen:**

    ```sh
    git clone https://github.com/HSBI-Lerngruppe-Bres/Durak.git
    cd Durak
    ```

2. **Poetry installieren:**

    ```sh
    curl -sSL https://install.python-poetry.org | python3 -
    ```

3. **Poetry zu Ihrem PATH hinzufügen (falls notwendig):**

    ```sh
    export PATH="$HOME/.local/bin:$PATH"
    ```

4. **Abhängigkeiten installieren:**

    ```sh
    poetry install
    ```

## Spiel starten

1. **Virtuelle Umgebung aktivieren:**

    ```sh
    poetry shell
    ```

2. **Flask-Anwendung starten:**

    ```sh
    poetry run python app.py
    ```

3. **Öffnen Sie Ihren Webbrowser und gehen Sie zu:**

    ```arduino
    http://127.0.0.1:5000/
    ```

## Beitragen

Beiträge sind willkommen! Bitte lesen Sie unsere [Beitragsrichtlinien](CONTRIBUTING.md) für weitere Informationen, wie Sie beginnen können.

## Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert. Siehe die [LICENSE](LICENSE)-Datei für Details.

---
