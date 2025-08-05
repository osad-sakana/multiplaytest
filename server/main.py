import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from game_state import GameManager
from models import PlayerInput

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

game_manager = GameManager()


@app.get("/")
async def root():
    return {"message": "Multiplayer Game Server"}


@app.get("/health")
async def health():
    return {"status": "healthy", "players": len(game_manager.state.players)}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    player = None

    try:
        # Wait for player name
        data = await websocket.receive_text()
        message = json.loads(data)

        if message.get("type") == "join":
            player_name = message.get("name", "Anonymous")
            player = await game_manager.add_player(websocket, player_name)

            # Send initial game state to the new player
            initial_state = await game_manager.get_game_state_for_player(player.id)
            await websocket.send_text(json.dumps(initial_state))

            print(f"Player {player_name} ({player.id}) joined the game")

        # Handle player inputs
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "input":
                player_input = PlayerInput(
                    player_id=player.id,
                    action=message.get("action"),
                    direction=message.get("direction"),
                )
                await game_manager.handle_player_input(player_input)

    except WebSocketDisconnect:
        if player:
            print(f"Player {player.name} ({player.id}) disconnected")
            await game_manager.remove_player(player.id)
    except Exception as e:
        print(f"Error handling websocket: {e}")
        if player:
            await game_manager.remove_player(player.id)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
