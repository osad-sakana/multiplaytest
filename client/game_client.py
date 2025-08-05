import asyncio
import json
import threading
from typing import Callable, Dict, Optional

import websockets


class GameClient:
    def __init__(self):
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.game_state: Dict = {}
        self.player_id: Optional[str] = None
        self.connected = False
        self.message_handlers: Dict[str, Callable] = {}
        self.receive_task: Optional[asyncio.Task] = None

    def set_message_handler(self, message_type: str, handler: Callable):
        self.message_handlers[message_type] = handler

    async def connect(self, server_url: str, player_name: str) -> bool:
        try:
            self.websocket = await websockets.connect(server_url)
            self.connected = True

            # Send join message
            join_message = {"type": "join", "name": player_name}
            await self.websocket.send(json.dumps(join_message))

            # Start receiving messages
            self.receive_task = asyncio.create_task(self._receive_messages())

            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False

    async def disconnect(self):
        self.connected = False
        if self.receive_task:
            self.receive_task.cancel()
        if self.websocket:
            await self.websocket.close()

    async def send_input(self, action: str, direction: str = None):
        if not self.connected or not self.websocket:
            return

        message = {"type": "input", "action": action, "direction": direction}

        try:
            await self.websocket.send(json.dumps(message))
        except Exception as e:
            print(f"Failed to send input: {e}")
            self.connected = False

    async def _receive_messages(self):
        try:
            while self.connected and self.websocket:
                message = await self.websocket.recv()
                data = json.loads(message)

                message_type = data.get("type")

                if message_type == "game_state":
                    self.game_state = data.get("data", {})
                    self.player_id = self.game_state.get("your_player_id")

                # Call registered handler
                if message_type in self.message_handlers:
                    self.message_handlers[message_type](data)

        except websockets.exceptions.ConnectionClosed:
            self.connected = False
        except Exception as e:
            print(f"Error receiving message: {e}")
            self.connected = False


class AsyncGameClient:
    def __init__(self):
        self.client = GameClient()
        self.loop = None
        self.thread = None

    def start_client_thread(self):
        self.thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.thread.start()

    def _run_event_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def connect(self, server_url: str, player_name: str, callback: Callable = None):
        if not self.loop:
            return False

        future = asyncio.run_coroutine_threadsafe(
            self.client.connect(server_url, player_name), self.loop
        )

        try:
            result = future.result(timeout=5.0)
            if callback:
                callback(result)
            return result
        except Exception as e:
            print(f"Connection failed: {e}")
            if callback:
                callback(False)
            return False

    def send_input(self, action: str, direction: str = None):
        if self.loop and self.client.connected:
            asyncio.run_coroutine_threadsafe(
                self.client.send_input(action, direction), self.loop
            )

    def set_message_handler(self, message_type: str, handler: Callable):
        self.client.set_message_handler(message_type, handler)

    def get_game_state(self) -> Dict:
        return self.client.game_state.copy()

    def get_player_id(self) -> Optional[str]:
        return self.client.player_id

    def is_connected(self) -> bool:
        return self.client.connected

    def disconnect(self):
        if self.loop:
            asyncio.run_coroutine_threadsafe(self.client.disconnect(), self.loop)
        if self.thread and self.thread.is_alive():
            self.loop.call_soon_threadsafe(self.loop.stop)
