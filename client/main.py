import pygame
import sys
import time
from game_client import AsyncGameClient
from renderer import GameRenderer

class Game:
    def __init__(self):
        self.client = AsyncGameClient()
        self.renderer = GameRenderer()
        self.running = True
        self.connected = False
        self.game_state = {}
        
        # Connection screen state
        self.connection_screen = True
        self.server_input = "localhost"
        self.port_input = "8000"
        self.name_input = "Player"
        self.current_field = 0  # 0: server, 1: port, 2: name
        self.error_message = ""
        
        # Game input state
        self.keys_pressed = set()
        self.dash_keys = {pygame.K_LSHIFT, pygame.K_RSHIFT}
        
        # Setup message handlers
        self.client.set_message_handler("game_state", self._handle_game_state)
        self.client.set_message_handler("player_update", self._handle_player_update)
        self.client.set_message_handler("player_joined", self._handle_player_joined)
        self.client.set_message_handler("player_left", self._handle_player_left)
        self.client.set_message_handler("respawn", self._handle_respawn)
    
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
    
    def handle_connection_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                self.current_field = (self.current_field + 1) % 3
            elif event.key == pygame.K_BACKSPACE:
                if self.current_field == 0 and self.server_input:
                    self.server_input = self.server_input[:-1]
                elif self.current_field == 1 and self.port_input:
                    self.port_input = self.port_input[:-1]
                elif self.current_field == 2 and self.name_input:
                    self.name_input = self.name_input[:-1]
            elif event.key == pygame.K_RETURN:
                self.attempt_connection()
            else:
                char = event.unicode
                if char.isprintable():
                    if self.current_field == 0:
                        self.server_input += char
                    elif self.current_field == 1:
                        self.port_input += char
                    elif self.current_field == 2:
                        self.name_input += char
    
    def attempt_connection(self):
        if not self.server_input or not self.port_input or not self.name_input:
            self.error_message = "Please fill in all fields"
            return
        
        try:
            port = int(self.port_input)
            server_url = f"ws://{self.server_input}:{port}/ws"
            
            self.client.start_client_thread()
            success = self.client.connect(server_url, self.name_input)
            
            if success:
                self.connection_screen = False
                self.connected = True
                self.error_message = ""
            else:
                self.error_message = "Failed to connect to server"
                
        except ValueError:
            self.error_message = "Invalid port number"
        except Exception as e:
            self.error_message = f"Connection error: {str(e)}"
    
    def handle_game_input(self, event):
        if event.type == pygame.KEYDOWN:
            self.keys_pressed.add(event.key)
            if event.key == pygame.K_ESCAPE:
                self.running = False
        elif event.type == pygame.KEYUP:
            self.keys_pressed.discard(event.key)
    
    def process_movement(self):
        if not self.connected:
            return
        
        # Check for dash modifier
        is_dashing = any(key in self.keys_pressed for key in self.dash_keys)
        action = "dash" if is_dashing else "move"
        
        # Movement keys
        if pygame.K_w in self.keys_pressed:
            self.client.send_input(action, "up")
        if pygame.K_s in self.keys_pressed:
            self.client.send_input(action, "down")
        if pygame.K_a in self.keys_pressed:
            self.client.send_input(action, "left")
        if pygame.K_d in self.keys_pressed:
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
                    self.error_message = "Connection lost"
            
            # Render
            if self.connection_screen:
                self.renderer.render_connection_screen(
                    self.server_input, self.port_input, self.name_input, self.error_message
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