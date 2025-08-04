import pygame
import math
from typing import Dict, Tuple

class GameRenderer:
    def __init__(self, width: int = 800, height: int = 600):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Multiplayer Game")
        
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.BLUE = (0, 0, 255)
        self.GRAY = (128, 128, 128)
        
    def render_game(self, game_state: Dict, player_id: str):
        self.screen.fill(self.BLACK)
        
        if not game_state:
            self._render_connection_status("Connecting...")
            pygame.display.flip()
            return
        
        players = game_state.get("players", {})
        field_width = game_state.get("field_width", 800)
        field_height = game_state.get("field_height", 600)
        player_size = game_state.get("player_size", 30)
        
        # Draw field boundary
        pygame.draw.rect(self.screen, self.WHITE, (0, 0, field_width, field_height), 2)
        
        # Draw players
        for pid, player_data in players.items():
            self._render_player(player_data, player_size, pid == player_id)
        
        # Draw UI
        self._render_ui(players, player_id)
        
        pygame.display.flip()
    
    def _render_player(self, player_data: Dict, player_size: int, is_current_player: bool):
        x = int(player_data.get("x", 0))
        y = int(player_data.get("y", 0))
        color = player_data.get("color", (255, 255, 255))
        is_dashing = player_data.get("is_dashing", False)
        name = player_data.get("name", "Unknown")
        
        # Draw player rectangle
        player_rect = pygame.Rect(x, y, player_size, player_size)
        
        if is_dashing:
            # Add dash effect
            pygame.draw.rect(self.screen, (255, 255, 255), player_rect.inflate(6, 6))
        
        pygame.draw.rect(self.screen, color, player_rect)
        
        # Draw border for current player
        if is_current_player:
            pygame.draw.rect(self.screen, self.WHITE, player_rect, 3)
        
        # Draw player name
        name_surface = self.small_font.render(name, True, self.WHITE)
        name_rect = name_surface.get_rect()
        name_rect.centerx = x + player_size // 2
        name_rect.bottom = y - 5
        self.screen.blit(name_surface, name_rect)
    
    def _render_ui(self, players: Dict, player_id: str):
        # Draw scoreboard
        y_offset = 10
        title_surface = self.font.render("Scoreboard", True, self.WHITE)
        self.screen.blit(title_surface, (self.width - 200, y_offset))
        y_offset += 40
        
        # Sort players by deaths (ascending)
        sorted_players = sorted(
            players.items(),
            key=lambda x: x[1].get("deaths", 0)
        )
        
        for i, (pid, player_data) in enumerate(sorted_players):
            name = player_data.get("name", "Unknown")
            deaths = player_data.get("deaths", 0)
            color = player_data.get("color", (255, 255, 255))
            
            # Highlight current player
            text_color = self.WHITE
            if pid == player_id:
                text_color = self.GREEN
            
            score_text = f"{name}: {deaths}"
            score_surface = self.small_font.render(score_text, True, text_color)
            self.screen.blit(score_surface, (self.width - 190, y_offset))
            
            # Draw small colored square next to name
            pygame.draw.rect(self.screen, color, (self.width - 200, y_offset + 2, 15, 15))
            
            y_offset += 25
        
        # Draw controls
        controls = [
            "WASD: Move",
            "Shift+WASD: Dash",
            "ESC: Quit"
        ]
        
        y_offset = self.height - len(controls) * 25 - 10
        for control in controls:
            control_surface = self.small_font.render(control, True, self.GRAY)
            self.screen.blit(control_surface, (10, y_offset))
            y_offset += 25
    
    def _render_connection_status(self, status: str):
        status_surface = self.font.render(status, True, self.WHITE)
        status_rect = status_surface.get_rect(center=(self.width // 2, self.height // 2))
        self.screen.blit(status_surface, status_rect)
    
    def render_connection_screen(self, server_input: str, port_input: str, name_input: str, error_message: str = ""):
        self.screen.fill(self.BLACK)
        
        title_surface = self.font.render("Connect to Server", True, self.WHITE)
        title_rect = title_surface.get_rect(center=(self.width // 2, 100))
        self.screen.blit(title_surface, title_rect)
        
        # Input fields
        fields = [
            ("Server IP:", server_input, 200),
            ("Port:", port_input, 250),
            ("Your Name:", name_input, 300)
        ]
        
        for label, value, y_pos in fields:
            label_surface = self.small_font.render(label, True, self.WHITE)
            self.screen.blit(label_surface, (200, y_pos))
            
            # Input box
            input_rect = pygame.Rect(200, y_pos + 25, 400, 30)
            pygame.draw.rect(self.screen, self.WHITE, input_rect, 2)
            
            value_surface = self.small_font.render(value, True, self.WHITE)
            self.screen.blit(value_surface, (input_rect.x + 5, input_rect.y + 5))
        
        # Instructions
        instructions = [
            "Enter server details and press ENTER to connect",
            "Use TAB to switch between fields"
        ]
        
        y_offset = 380
        for instruction in instructions:
            inst_surface = self.small_font.render(instruction, True, self.GRAY)
            inst_rect = inst_surface.get_rect(center=(self.width // 2, y_offset))
            self.screen.blit(inst_surface, inst_rect)
            y_offset += 30
        
        # Error message
        if error_message:
            error_surface = self.small_font.render(error_message, True, self.RED)
            error_rect = error_surface.get_rect(center=(self.width // 2, 450))
            self.screen.blit(error_surface, error_rect)
        
        pygame.display.flip()
    
    def quit(self):
        pygame.quit()