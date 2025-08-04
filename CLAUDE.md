# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Environment Setup
```bash
# Install dependencies
poetry install

# Install with development dependencies
poetry install --with dev

# Setup pre-commit hooks
poetry run pre-commit install
```

### Running the Application
```bash
# Start server with Docker
docker-compose up --build

# Start server in development mode (without Docker)
poetry run python server/main.py

# Start client
poetry run python client/main.py
```

### Code Quality
```bash
# Run linting and formatting
poetry run black .
poetry run flake8 .
poetry run isort .

# Run pre-commit hooks manually
poetry run pre-commit run --all-files
```

## Architecture Overview

This is a real-time multiplayer game built with FastAPI/WebSocket on the backend and Pygame on the frontend.

### Server Architecture (`server/`)
- **`main.py`**: FastAPI application with WebSocket endpoint at `/ws`. Handles player connections and message routing.
- **`game_state.py`**: Contains `GameManager` class - the core game engine that manages player state, movement, collision detection, and game events.
- **`models.py`**: Pydantic models for `Player`, `GameState`, `PlayerInput`, and `GameUpdate` messages.

### Client Architecture (`client/`)
- **`main.py`**: Main game loop and event handling. Contains the `Game` class that manages connection state, input processing, and screen transitions.
- **`game_client.py`**: WebSocket communication layer with `AsyncGameClient` wrapper for threading support.
- **`renderer.py`**: Pygame rendering engine that handles game graphics and UI elements.

### Communication Protocol
The client-server communication uses WebSocket with JSON messages:
- **Join**: `{"type": "join", "name": "PlayerName"}`
- **Input**: `{"type": "input", "action": "move|dash", "direction": "up|down|left|right"}`
- **Updates**: Server broadcasts `game_state`, `player_update`, `player_joined`, `player_left`, `respawn` messages

### Game Logic
- Players spawn at field center (400, 300) with random RGB colors
- Movement speed: 5.0 units (normal), 15.0 units (dash)
- Dash has 0.3s duration and 1.0s cooldown
- Out-of-bounds detection triggers respawn and increments death counter
- Game field is 800x600 pixels with 30x30 pixel player squares

### Development Notes
- Server runs on port 8000 by default
- Client connects to `ws://localhost:8000/ws` by default
- Game state is synchronized in real-time across all connected clients
- Docker setup allows server deployment while client runs locally
- Poetry manages all dependencies and development tools