# -*- coding: utf-8 -*-
import pygame
from game_client import AsyncGameClient
from renderer import GameRenderer
from server_manager import ServerManager


class Game:
    def __init__(self):
        self.client = AsyncGameClient()
        self.renderer = GameRenderer()
        self.running = True
        self.connected = False
        self.game_state = {}

        # Server management
        self.server_manager = ServerManager()

        # Connection screen state
        self.connection_screen = True
        self.server_list_mode = False  # Toggle between connection and server list
        self.server_address_input = self.server_manager.get_default_address()
        self.name_input = "Player"
        self.current_field = 0  # 0: server_address, 1: name
        self.error_message = ""

        # Server list state
        self.selected_server_index = 0
        self.new_server_name = ""
        self.new_server_address = ""
        self.server_input_field = 0  # 0: name, 1: address

        # Game input state
        self.keys_pressed = set()
        self.boost_keys = {pygame.K_LSHIFT, pygame.K_RSHIFT}

        # Setup message handlers
        self.client.set_message_handler("game_state", self._handle_game_state)
        self.client.set_message_handler("player_update", self._handle_player_update)
        self.client.set_message_handler("player_joined", self._handle_player_joined)
        self.client.set_message_handler("player_left", self._handle_player_left)
        self.client.set_message_handler("respawn", self._handle_respawn)
        self.client.set_message_handler("player_death", self._handle_player_death)
        self.client.set_message_handler("message", self._handle_message)

    def _handle_game_state(self, data):
        self.game_state = data.get("data", {})

    def _handle_player_update(self, data):
        player_data = data.get("data", {}).get("player", {})
        player_id = player_data.get("id")
        if player_id and "players" in self.game_state:
            self.game_state["players"][player_id] = player_data

    def _handle_player_joined(self, data):
        player_data = data.get("data", {}).get("player", {})
        player_id = player_data.get("id")
        if player_id:
            if "players" not in self.game_state:
                self.game_state["players"] = {}
            self.game_state["players"][player_id] = player_data

    def _handle_player_left(self, data):
        player_id = data.get("data", {}).get("player_id")
        if player_id and "players" in self.game_state:
            self.game_state["players"].pop(player_id, None)

    def _handle_respawn(self, data):
        player_data = data.get("data", {}).get("player", {})
        player_id = player_data.get("id")
        if player_id and "players" in self.game_state:
            self.game_state["players"][player_id] = player_data

    def _handle_player_death(self, data):
        player_data = data.get("data", {}).get("player", {})
        player_id = player_data.get("id")
        if player_id and "players" in self.game_state:
            self.game_state["players"][player_id] = player_data

    def _handle_message(self, data):
        message_data = data.get("data", {}).get("message", {})
        if "messages" not in self.game_state:
            self.game_state["messages"] = []
        self.game_state["messages"].append(message_data)

    def handle_connection_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                self.server_list_mode = not self.server_list_mode
                self.error_message = ""
            elif self.server_list_mode:
                self._handle_server_list_input(event)
            else:
                self._handle_connection_form_input(event)

    def _handle_connection_form_input(self, event):
        if event.key == pygame.K_TAB:
            self.current_field = (self.current_field + 1) % 2
        elif event.key == pygame.K_BACKSPACE:
            if self.current_field == 0 and self.server_address_input:
                self.server_address_input = self.server_address_input[:-1]
            elif self.current_field == 1 and self.name_input:
                self.name_input = self.name_input[:-1]
        elif event.key == pygame.K_RETURN:
            self.attempt_connection()
        else:
            char = event.unicode
            if char.isprintable():
                if self.current_field == 0:
                    self.server_address_input += char
                elif self.current_field == 1:
                    self.name_input += char

    def _handle_server_list_input(self, event):
        servers = self.server_manager.get_servers()
        if event.key == pygame.K_UP and servers:
            self.selected_server_index = (self.selected_server_index - 1) % len(servers)
        elif event.key == pygame.K_DOWN and servers:
            self.selected_server_index = (self.selected_server_index + 1) % len(servers)
        elif event.key == pygame.K_RETURN and servers:
            # Select server
            selected_server = servers[self.selected_server_index]
            self.server_address_input = selected_server["address"]
            self.server_list_mode = False
        elif event.key == pygame.K_DELETE and servers:
            # Delete selected server
            if len(servers) > 1:  # Keep at least one server
                self.server_manager.remove_server(self.selected_server_index)
                if self.selected_server_index >= len(self.server_manager.get_servers()):
                    self.selected_server_index = max(
                        0, len(self.server_manager.get_servers()) - 1
                    )
        elif event.key == pygame.K_TAB:
            self.server_input_field = (self.server_input_field + 1) % 2
        elif event.key == pygame.K_BACKSPACE:
            if self.server_input_field == 0 and self.new_server_name:
                self.new_server_name = self.new_server_name[:-1]
            elif self.server_input_field == 1 and self.new_server_address:
                self.new_server_address = self.new_server_address[:-1]
        elif event.key == pygame.K_INSERT:
            # Add new server
            if self.new_server_name and self.new_server_address:
                if self.server_manager.add_server(
                    self.new_server_name, self.new_server_address
                ):
                    self.new_server_name = ""
                    self.new_server_address = ""
                    self.error_message = "サーバーが追加されました！"
                else:
                    self.error_message = "サーバーが既に存在します！"
        else:
            char = event.unicode
            if char.isprintable():
                if self.server_input_field == 0:
                    self.new_server_name += char
                elif self.server_input_field == 1:
                    self.new_server_address += char

    def attempt_connection(self):
        if not self.server_address_input or not self.name_input:
            self.error_message = "すべてのフィールドを入力してください"
            return

        try:
            # Parse address:port format
            if ":" not in self.server_address_input:
                self.error_message = "アドレスは IP:PORT 形式で入力してください"
                return

            server_ip, port_str = self.server_address_input.rsplit(":", 1)
            port = int(port_str)
            server_url = f"ws://{server_ip}:{port}/ws"

            self.client.start_client_thread()
            success = self.client.connect(server_url, self.name_input)

            if success:
                self.connection_screen = False
                self.connected = True
                self.error_message = ""
            else:
                self.error_message = "サーバーへの接続に失敗しました"

        except ValueError:
            self.error_message = "アドレス形式またはポート番号が無効です"
        except Exception as e:
            self.error_message = f"接続エラー: {str(e)}"

    def handle_game_input(self, event):
        if event.type == pygame.KEYDOWN:
            self.keys_pressed.add(event.key)
            if event.key == pygame.K_ESCAPE:
                self.running = False
            elif event.key == pygame.K_SPACE:
                # Send respawn input
                self.client.send_input("respawn")
        elif event.type == pygame.KEYUP:
            self.keys_pressed.discard(event.key)

    def process_movement(self):
        if not self.connected:
            return

        # Check for boost modifier
        is_boosting = any(key in self.keys_pressed for key in self.boost_keys)
        action = "boost" if is_boosting else "move"

        # Movement keys (WASD + Arrow keys)
        if pygame.K_w in self.keys_pressed or pygame.K_UP in self.keys_pressed:
            self.client.send_input(action, "up")
        if pygame.K_s in self.keys_pressed or pygame.K_DOWN in self.keys_pressed:
            self.client.send_input(action, "down")
        if pygame.K_a in self.keys_pressed or pygame.K_LEFT in self.keys_pressed:
            self.client.send_input(action, "left")
        if pygame.K_d in self.keys_pressed or pygame.K_RIGHT in self.keys_pressed:
            self.client.send_input(action, "right")

    def run(self):
        clock = pygame.time.Clock()

        while self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif self.connection_screen:
                    self.handle_connection_input(event)
                else:
                    self.handle_game_input(event)

            # Process game logic
            if not self.connection_screen:
                self.process_movement()

                # Update connection status
                if not self.client.is_connected():
                    self.connected = False
                    self.connection_screen = True
                    self.error_message = "接続が失われました"

            # Render
            if self.connection_screen:
                servers = (
                    self.server_manager.get_servers() if self.server_list_mode else None
                )
                self.renderer.render_connection_screen(
                    server_address_input=self.server_address_input,
                    name_input=self.name_input,
                    error_message=self.error_message,
                    server_list_mode=self.server_list_mode,
                    servers=servers,
                    selected_server_index=self.selected_server_index,
                    new_server_name=self.new_server_name,
                    new_server_address=self.new_server_address,
                    server_input_field=self.server_input_field,
                    current_field=self.current_field,
                )
            else:
                player_id = self.client.get_player_id()
                self.renderer.render_game(self.game_state, player_id)

            clock.tick(60)  # 60 FPS

        # Cleanup
        if self.connected:
            self.client.disconnect()
        self.renderer.quit()


if __name__ == "__main__":
    game = Game()
    game.run()
