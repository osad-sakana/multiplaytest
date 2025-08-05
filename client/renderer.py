import math
import time
from typing import Dict

import pygame


class GameRenderer:
    def __init__(self, width: int = 800, height: int = 600):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Multiplayer Game")

        # Load Japanese font
        try:
            self.font = pygame.font.Font("PixelMplus12-Regular.ttf", 36)
            self.small_font = pygame.font.Font("PixelMplus12-Regular.ttf", 24)
            self.tiny_font = pygame.font.Font("PixelMplus12-Regular.ttf", 18)
        except FileNotFoundError:
            # Fallback to default font if Japanese font not found
            self.font = pygame.font.Font(None, 36)
            self.small_font = pygame.font.Font(None, 24)
            self.tiny_font = pygame.font.Font(None, 18)

        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.BLUE = (0, 0, 255)
        self.GRAY = (128, 128, 128)
        self.DARK_GRAY = (64, 64, 64)
        self.YELLOW = (255, 255, 0)

    def render_game(self, game_state: Dict, player_id: str):
        self.screen.fill(self.BLACK)

        if not game_state:
            self._render_connection_status("接続中...")
            pygame.display.flip()
            return

        players = game_state.get("players", {})
        field_width = game_state.get("field_width", 800)
        field_height = game_state.get("field_height", 600)
        player_size = game_state.get("player_size", 30)
        stage_center_x = game_state.get("stage_center_x", 400)
        stage_center_y = game_state.get("stage_center_y", 300)
        stage_radius = game_state.get("stage_radius", 250)
        messages = game_state.get("messages", [])

        # Draw circular stage
        self._render_stage(stage_center_x, stage_center_y, stage_radius)

        # Draw players
        for pid, player_data in players.items():
            self._render_player(player_data, player_size, pid == player_id)

        # Draw UI
        self._render_ui(players, player_id)

        # Draw messages
        self._render_messages(messages)

        pygame.display.flip()

    def _render_stage(self, center_x: int, center_y: int, radius: int):
        """Draw the circular stage"""
        # Draw outer circle (stage boundary)
        pygame.draw.circle(self.screen, self.WHITE, (center_x, center_y), radius, 3)

        # Draw inner circle for visual reference
        pygame.draw.circle(
            self.screen, self.DARK_GRAY, (center_x, center_y), radius - 20, 1
        )

        # Draw center point
        pygame.draw.circle(self.screen, self.GRAY, (center_x, center_y), 5)

    def _render_player(
        self, player_data: Dict, player_size: int, is_current_player: bool
    ):
        x = int(player_data.get("x", 0))
        y = int(player_data.get("y", 0))
        color = player_data.get("color", (255, 255, 255))
        stamina = player_data.get("stamina", 100)
        max_stamina = player_data.get("max_stamina", 100)
        velocity_x = player_data.get("velocity_x", 0)
        velocity_y = player_data.get("velocity_y", 0)
        name = player_data.get("name", "Unknown")
        is_dead = player_data.get("is_dead", False)
        respawn_cooldown = player_data.get("respawn_cooldown", 0)
        respawn_ready = player_data.get("respawn_ready", True)

        # Don't render dead players visually on stage
        if is_dead:
            # Show respawn status for current player
            if is_current_player:
                self._render_respawn_status(respawn_cooldown, respawn_ready)
            return

        # Draw player rectangle
        player_rect = pygame.Rect(x, y, player_size, player_size)

        # Add velocity trail effect
        velocity_magnitude = math.sqrt(velocity_x**2 + velocity_y**2)
        if velocity_magnitude > 1:
            trail_length = min(velocity_magnitude * 2, 20)
            trail_x = (
                x + player_size / 2 - velocity_x * trail_length / velocity_magnitude
            )
            trail_y = (
                y + player_size / 2 - velocity_y * trail_length / velocity_magnitude
            )
            pygame.draw.line(
                self.screen,
                (*color, 128),
                (trail_x, trail_y),
                (x + player_size / 2, y + player_size / 2),
                3,
            )

        pygame.draw.rect(self.screen, color, player_rect)

        # Draw border for current player
        if is_current_player:
            pygame.draw.rect(self.screen, self.WHITE, player_rect, 3)

        # Draw stamina bar for current player
        if is_current_player:
            bar_width = player_size
            bar_height = 4
            bar_x = x
            bar_y = y - 10

            # Background
            pygame.draw.rect(
                self.screen, self.DARK_GRAY, (bar_x, bar_y, bar_width, bar_height)
            )

            # Stamina bar
            stamina_ratio = stamina / max_stamina if max_stamina > 0 else 0
            stamina_width = int(bar_width * stamina_ratio)
            stamina_color = (
                self.GREEN
                if stamina_ratio > 0.3
                else self.YELLOW
                if stamina_ratio > 0.1
                else self.RED
            )
            pygame.draw.rect(
                self.screen, stamina_color, (bar_x, bar_y, stamina_width, bar_height)
            )

        # Draw player name
        name_surface = self.small_font.render(name, True, self.WHITE)
        name_rect = name_surface.get_rect()
        name_rect.centerx = x + player_size // 2
        name_rect.bottom = y - (15 if is_current_player else 5)
        self.screen.blit(name_surface, name_rect)

    def _render_ui(self, players: Dict, player_id: str):
        # Draw scoreboard
        y_offset = 10
        title_surface = self.font.render("Scoreboard", True, self.WHITE)
        self.screen.blit(title_surface, (self.width - 200, y_offset))
        y_offset += 40

        # Sort players by deaths (ascending)
        sorted_players = sorted(players.items(), key=lambda x: x[1].get("deaths", 0))

        for pid, player_data in sorted_players:
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
            pygame.draw.rect(
                self.screen, color, (self.width - 200, y_offset + 2, 15, 15)
            )

            y_offset += 25

        # Draw current player stamina display
        if player_id in players:
            current_player = players[player_id]
            stamina = current_player.get("stamina", 100)
            max_stamina = current_player.get("max_stamina", 100)

            y_offset += 20
            stamina_text = f"Stamina: {int(stamina)}/{int(max_stamina)}"
            stamina_surface = self.small_font.render(stamina_text, True, self.WHITE)
            self.screen.blit(stamina_surface, (self.width - 190, y_offset))

        # Draw controls
        controls = ["WASD/矢印キー: 移動", "Shift+移動: ブースト", "SPACE: 復活", "ESC: 終了"]

        y_offset = self.height - len(controls) * 25 - 10
        for control in controls:
            control_surface = self.small_font.render(control, True, self.GRAY)
            self.screen.blit(control_surface, (10, y_offset))
            y_offset += 25

    def _render_messages(self, messages: list):
        """Render game messages (join, leave, death notifications)"""
        current_time = time.time()
        y_offset = 50
        max_messages = 5

        # Filter recent messages and limit count
        recent_messages = []
        for msg in messages[-max_messages:]:
            if isinstance(msg, dict):
                timestamp = msg.get("timestamp", 0)
                duration = msg.get("duration", 3.0)
                if current_time - timestamp < duration:
                    recent_messages.append(msg)

        # Render messages
        for msg in recent_messages:
            text = msg.get("text", "")
            timestamp = msg.get("timestamp", 0)
            duration = msg.get("duration", 3.0)

            # Calculate fade effect
            age = current_time - timestamp
            alpha = max(0, 1 - (age / duration))

            # Calculate fade effect for alpha blending

            # Create text surface
            text_surface = self.small_font.render(text, True, self.WHITE)

            # Create background for better readability
            text_rect = text_surface.get_rect()
            bg_rect = text_rect.inflate(10, 4)
            bg_rect.centerx = self.width // 2
            bg_rect.y = y_offset

            # Draw semi-transparent background
            bg_surface = pygame.Surface((bg_rect.width, bg_rect.height))
            bg_surface.set_alpha(int(128 * alpha))
            bg_surface.fill(self.BLACK)
            self.screen.blit(bg_surface, bg_rect)

            # Draw text
            text_rect.center = bg_rect.center
            text_surface.set_alpha(int(255 * alpha))
            self.screen.blit(text_surface, text_rect)

            y_offset += 30

    def _render_connection_status(self, status: str):
        status_surface = self.font.render(status, True, self.WHITE)
        status_rect = status_surface.get_rect(
            center=(self.width // 2, self.height // 2)
        )
        self.screen.blit(status_surface, status_rect)

    def render_connection_screen(
        self,
        server_address_input: str,
        name_input: str,
        error_message: str = "",
        server_list_mode: bool = False,
        servers: list = None,
        selected_server_index: int = 0,
        new_server_name: str = "",
        new_server_address: str = "",
        server_input_field: int = 0,
        current_field: int = 0,
    ):
        self.screen.fill(self.BLACK)

        if server_list_mode:
            self._render_server_list(
                servers or [],
                selected_server_index,
                new_server_name,
                new_server_address,
                server_input_field,
                error_message,
            )
        else:
            self._render_connection_form(
                server_address_input, name_input, error_message, current_field
            )

        # Error message
        if error_message:
            error_surface = self.small_font.render(error_message, True, self.RED)
            error_rect = error_surface.get_rect(center=(self.width // 2, 450))
            self.screen.blit(error_surface, error_rect)

        pygame.display.flip()

    def _render_connection_form(
        self,
        server_address_input: str,
        name_input: str,
        error_message: str,
        current_field: int = 0,
    ):
        """Render the connection form"""
        title_surface = self.font.render("サーバーに接続", True, self.WHITE)
        title_rect = title_surface.get_rect(center=(self.width // 2, 100))
        self.screen.blit(title_surface, title_rect)

        # Input fields
        fields = [
            ("サーバーアドレス:", server_address_input, 200),
            ("プレイヤー名:", name_input, 250),
        ]

        # Use the current_field parameter

        for i, (label, value, y_pos) in enumerate(fields):
            label_surface = self.small_font.render(label, True, self.WHITE)
            self.screen.blit(label_surface, (200, y_pos))

            # Input box with highlight for current field
            input_rect = pygame.Rect(200, y_pos + 25, 400, 30)
            border_color = self.GREEN if i == current_field else self.WHITE
            border_width = 3 if i == current_field else 2
            pygame.draw.rect(self.screen, border_color, input_rect, border_width)

            # Add subtle background highlight for selected field
            if i == current_field:
                highlight_rect = pygame.Rect(
                    input_rect.x + 2,
                    input_rect.y + 2,
                    input_rect.width - 4,
                    input_rect.height - 4,
                )
                highlight_surface = pygame.Surface(
                    (highlight_rect.width, highlight_rect.height)
                )
                highlight_surface.set_alpha(30)
                highlight_surface.fill(self.GREEN)
                self.screen.blit(highlight_surface, highlight_rect)

            value_surface = self.small_font.render(value, True, self.WHITE)
            self.screen.blit(value_surface, (input_rect.x + 5, input_rect.y + 5))

        # Instructions
        instructions = [
            "サーバーアドレス (IP:PORT) と名前を入力",
            "ENTER: 接続、TAB: フィールド切替",
            "S: サーバーリストを開く",
        ]

        y_offset = 330
        for instruction in instructions:
            inst_surface = self.small_font.render(instruction, True, self.GRAY)
            inst_rect = inst_surface.get_rect(center=(self.width // 2, y_offset))
            self.screen.blit(inst_surface, inst_rect)
            y_offset += 25

        # Error message
        if error_message:
            error_surface = self.small_font.render(error_message, True, self.RED)
            error_rect = error_surface.get_rect(center=(self.width // 2, 450))
            self.screen.blit(error_surface, error_rect)

    def _render_server_list(
        self,
        servers: list,
        selected_index: int,
        new_name: str,
        new_address: str,
        input_field: int,
        error_message: str,
    ):
        """Render the server list management screen"""
        title_surface = self.font.render("サーバーリスト", True, self.WHITE)
        title_rect = title_surface.get_rect(center=(self.width // 2, 50))
        self.screen.blit(title_surface, title_rect)

        # Server list
        y_offset = 100
        list_height = 200
        list_rect = pygame.Rect(50, y_offset, self.width - 100, list_height)
        pygame.draw.rect(self.screen, self.DARK_GRAY, list_rect)
        pygame.draw.rect(self.screen, self.WHITE, list_rect, 2)

        # Draw servers
        item_height = 25
        for i, server in enumerate(servers):
            item_y = y_offset + 10 + i * item_height
            if item_y + item_height > y_offset + list_height - 10:
                break  # Don't draw outside the box

            # Highlight selected server
            if i == selected_index:
                highlight_rect = pygame.Rect(
                    55, item_y - 2, self.width - 110, item_height
                )
                pygame.draw.rect(self.screen, self.BLUE, highlight_rect)

            # Server info
            server_text = f"{server['name']} - {server['address']}"
            text_color = self.WHITE if i == selected_index else self.GRAY
            server_surface = self.small_font.render(server_text, True, text_color)
            self.screen.blit(server_surface, (60, item_y))

        # Add new server section
        add_y = y_offset + list_height + 20
        add_title = self.small_font.render("新しいサーバーを追加:", True, self.WHITE)
        self.screen.blit(add_title, (50, add_y))

        # New server input fields
        fields = [
            ("名前:", new_name, add_y + 30),
            ("アドレス:", new_address, add_y + 70),
        ]

        for i, (label, value, field_y) in enumerate(fields):
            label_surface = self.tiny_font.render(label, True, self.WHITE)
            self.screen.blit(label_surface, (50, field_y))

            # Input box
            input_rect = pygame.Rect(120, field_y - 2, 300, 25)
            border_color = self.GREEN if i == input_field else self.WHITE
            pygame.draw.rect(self.screen, border_color, input_rect, 2)

            value_surface = self.tiny_font.render(value, True, self.WHITE)
            self.screen.blit(value_surface, (input_rect.x + 5, input_rect.y + 3))

        # Instructions
        instructions = [
            "↑↓: サーバー選択、ENTER: 接続、DELETE: 削除",
            "TAB: 入力フィールド切替、INSERT: サーバー追加",
            "S: 接続画面に戻る",
        ]

        inst_y = add_y + 110
        for instruction in instructions:
            inst_surface = self.tiny_font.render(instruction, True, self.GRAY)
            self.screen.blit(inst_surface, (50, inst_y))
            inst_y += 20

        # Error/success message
        if error_message:
            msg_color = self.GREEN if "success" in error_message.lower() else self.RED
            error_surface = self.small_font.render(error_message, True, msg_color)
            error_rect = error_surface.get_rect(center=(self.width // 2, 500))
            self.screen.blit(error_surface, error_rect)

    def _render_respawn_status(self, respawn_cooldown: float, respawn_ready: bool):
        """Render respawn cooldown and status"""
        current_time = time.time()

        # Center of screen
        center_x = self.width // 2
        center_y = self.height // 2

        if respawn_ready:
            # Show respawn ready message
            ready_text = "SPACEキーで復活"
            ready_surface = self.font.render(ready_text, True, self.GREEN)
            ready_rect = ready_surface.get_rect(center=(center_x, center_y))
            self.screen.blit(ready_surface, ready_rect)

            # Pulsing effect
            pulse = int(127 + 128 * math.sin(current_time * 5))
            glow_color = (0, pulse, 0)
            glow_surface = self.font.render(ready_text, True, glow_color)
            glow_rect = glow_surface.get_rect(center=(center_x + 1, center_y + 1))
            self.screen.blit(glow_surface, glow_rect)
        else:
            # Show cooldown timer
            remaining = max(0, respawn_cooldown - current_time)
            timer_text = f"復活まで {remaining:.1f}秒"
            timer_surface = self.font.render(timer_text, True, self.WHITE)
            timer_rect = timer_surface.get_rect(center=(center_x, center_y - 30))
            self.screen.blit(timer_surface, timer_rect)

            # Cooldown gauge
            gauge_width = 300
            gauge_height = 20
            gauge_x = center_x - gauge_width // 2
            gauge_y = center_y

            # Background
            gauge_bg = pygame.Rect(gauge_x, gauge_y, gauge_width, gauge_height)
            pygame.draw.rect(self.screen, self.DARK_GRAY, gauge_bg)
            pygame.draw.rect(self.screen, self.WHITE, gauge_bg, 2)

            # Progress
            total_cooldown = 3.0  # Should match server's respawn_cooldown_time
            progress = max(0, 1 - (remaining / total_cooldown))
            progress_width = int(gauge_width * progress)
            if progress_width > 0:
                progress_rect = pygame.Rect(
                    gauge_x, gauge_y, progress_width, gauge_height
                )
                progress_color = self.GREEN if progress >= 1.0 else self.YELLOW
                pygame.draw.rect(self.screen, progress_color, progress_rect)

    def quit(self):
        pygame.quit()
