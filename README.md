# Durak

![Durak Logo](static/images/261787.ico)

## Overview

**Durak** is a multiplayer card game where players compete to avoid being the last one with cards in their hand. The game is built using Flask, SocketIO, and SQLAlchemy, and features real-time interactions and a modern web interface.

## Features

- Real-time multiplayer gameplay
- User authentication and session management
- Interactive UI with real-time updates
- Cross-platform support (Windows, macOS, Linux)

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
  - [Windows](#windows)
  - [macOS](#macos)
  - [Linux](#linux)
- [Running the Game](#running-the-game)
- [Contributing](#contributing)
- [License](#license)

## Requirements

- Python 3.9 or higher
- Poetry for dependency management

## Installation

### Windows

1. **Clone the repository:**

    ```sh
    git clone https://github.com/HSBI-Lerngruppe-Bres/Durak.git
    cd Durak
    ```

2. **Install Poetry:**

    ```sh
    pip install --user pipx
    pipx install poetry
    ```

3. **Install dependencies:**

    ```sh
    poetry install
    ```

### macOS

1. **Clone the repository:**

    ```sh
    git clone https://github.com/HSBI-Lerngruppe-Bres/Durak.git
    cd Durak
    ```

2. **Install Poetry:**

    ```sh
    brew install pipx
    pipx install poetry
    ```

3. **Install dependencies:**

    ```sh
    poetry install
    ```

### Linux

1. **Clone the repository:**

    ```sh
    git clone https://github.com/HSBI-Lerngruppe-Bres/Durak.git
    cd Durak
    ```

2. **Install Poetry:**

    ```sh
    curl -sSL https://install.python-poetry.org | python3 -
    ```

3. **Add Poetry to your PATH (if necessary):**

    ```sh
    export PATH="$HOME/.local/bin:$PATH"
    ```

4. **Install dependencies:**

    ```sh
    poetry install
    ```

## Running the Game

1. **Activate the virtual environment:**

    ```sh
    poetry shell
    ```

2. **Run the Flask application:**

    ```sh
    poetry run python app.py
    ```

3. **Open your web browser and go to:**

    ```arduino
    http://127.0.0.1:5000/
    ```

## Contributing

We welcome contributions! Please read our Contributing Guidelines for more information on how to get started.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
