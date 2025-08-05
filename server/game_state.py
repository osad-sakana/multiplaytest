import asyncio
import math
import time
import uuid
from typing import Dict

from models import GameMessage, GameState, GameUpdate, Player, PlayerInput


class GameManager:
    def __init__(self):
        self.state = GameState()
        self.connected_clients: Dict[str, any] = {}
        self.base_speed = 1.5  # Reduced from 3.0
        self.boost_multiplier = 2.0
        self.stamina_drain_rate = 30.0  # stamina per second when boosting
        self.stamina_regen_rate = 20.0  # stamina per second when not boosting
        self.friction = 0.92  # Reduced from 0.95 for more friction
        self.max_velocity = 8.0  # Max velocity when boosting
        self.normal_max_velocity = 3.0  # Max velocity when not boosting
        self.respawn_cooldown_time = 3.0  # 3 seconds cooldown

        # Game loop will be started when the event loop is running
        self.game_loop_task = None

    async def game_loop(self):
        """Main game loop that updates physics and game state"""
        while True:
            await self.update_physics()
            await asyncio.sleep(1 / 60)  # 60 FPS

    async def update_physics(self):
        """Update player physics, collisions, and stamina"""
        current_time = time.time()

        for player in self.state.players.values():
            # Handle dead players
            if player.is_dead:
                # Update respawn cooldown
                if player.respawn_cooldown > current_time:
                    continue
                else:
                    player.respawn_ready = True
                    continue

            # Apply friction
            player.velocity_x *= self.friction
            player.velocity_y *= self.friction

            # Update position based on velocity
            player.x += player.velocity_x
            player.y += player.velocity_y

            # Regenerate stamina
            if player.stamina < player.max_stamina:
                player.stamina = min(
                    player.max_stamina, player.stamina + self.stamina_regen_rate / 60
                )

            # Check circular stage bounds
            if self.is_outside_stage(player):
                await self.kill_player(player)
                continue

        # Handle player collisions
        await self.handle_player_collisions()

        # Broadcast updates if there are changes
        if self.state.players:
            await self.broadcast_all_players_update()

    async def handle_player_collisions(self):
        """Handle collisions between players and push them apart"""
        players = list(self.state.players.values())
        for i in range(len(players)):
            for j in range(i + 1, len(players)):
                player1, player2 = players[i], players[j]

                # Calculate distance between players
                dx = player2.x - player1.x
                dy = player2.y - player1.y
                distance = math.sqrt(dx * dx + dy * dy)

                # Check if collision occurs
                min_distance = self.state.player_size
                if distance < min_distance and distance > 0:
                    # Calculate push direction (normalize)
                    push_x = dx / distance
                    push_y = dy / distance

                    # Calculate how much to push apart
                    overlap = min_distance - distance
                    push_strength = overlap * 0.5

                    # Push players apart
                    player1.x -= push_x * push_strength
                    player1.y -= push_y * push_strength
                    player2.x += push_x * push_strength
                    player2.y += push_y * push_strength

                    # Add some velocity for more dynamic collision
                    push_velocity = 2.0
                    player1.velocity_x -= push_x * push_velocity
                    player1.velocity_y -= push_y * push_velocity
                    player2.velocity_x += push_x * push_velocity
                    player2.velocity_y += push_y * push_velocity

    async def add_player(self, websocket, player_name: str) -> Player:
        # Start game loop if not already running
        if self.game_loop_task is None:
            self.game_loop_task = asyncio.create_task(self.game_loop())

        player = Player(
            name=player_name, x=self.state.stage_center_x, y=self.state.stage_center_y
        )

        self.state.players[player.id] = player
        self.connected_clients[player.id] = websocket

        # Add join message
        await self.add_message(f"{player_name} がゲームに参加しました！")

        # Notify all clients about new player
        update = GameUpdate(type="player_joined", data={"player": player.model_dump()})
        await self.broadcast_update(update)

        return player

    async def remove_player(self, player_id: str):
        player_name = None
        if player_id in self.state.players:
            player_name = self.state.players[player_id].name
            del self.state.players[player_id]
        if player_id in self.connected_clients:
            del self.connected_clients[player_id]

        if player_name:
            await self.add_message(f"{player_name} がゲームから退出しました")

        update = GameUpdate(type="player_left", data={"player_id": player_id})
        await self.broadcast_update(update)

    async def add_message(self, text: str):
        """Add a game message to be displayed to players"""
        message = GameMessage(id=str(uuid.uuid4()), text=text, timestamp=time.time())
        self.state.messages.append(message.model_dump())

        # Broadcast message
        update = GameUpdate(type="message", data={"message": message.model_dump()})
        await self.broadcast_update(update)

    async def handle_player_input(self, player_input: PlayerInput):
        player_id = player_input.player_id
        if player_id not in self.state.players:
            return

        player = self.state.players[player_id]

        # Handle respawn input
        if player.is_dead and player_input.action == "respawn":
            if player.respawn_ready:
                await self.respawn_player(player)
            return

        # Ignore movement input if player is dead
        if player.is_dead:
            return

        if player_input.direction:
            await self.apply_movement(
                player, player_input.direction, player_input.action == "boost"
            )

    async def apply_movement(self, player: Player, direction: str, is_boosting: bool):
        """Apply movement force to player with inertia"""
        # Calculate movement force
        force = self.base_speed
        if is_boosting and player.stamina > 0:
            force *= self.boost_multiplier
            # Drain stamina
            player.stamina = max(0, player.stamina - self.stamina_drain_rate / 60)

        # Apply force based on direction
        if direction == "up":
            player.velocity_y -= force
        elif direction == "down":
            player.velocity_y += force
        elif direction == "left":
            player.velocity_x -= force
        elif direction == "right":
            player.velocity_x += force

        # Limit maximum velocity based on boost status
        velocity_magnitude = math.sqrt(player.velocity_x**2 + player.velocity_y**2)
        max_vel = self.max_velocity if is_boosting else self.normal_max_velocity
        if velocity_magnitude > max_vel:
            scale = max_vel / velocity_magnitude
            player.velocity_x *= scale
            player.velocity_y *= scale

    def is_outside_stage(self, player: Player) -> bool:
        """Check if player is outside the circular stage"""
        center_x = self.state.stage_center_x
        center_y = self.state.stage_center_y

        # Calculate distance from stage center
        dx = player.x + self.state.player_size / 2 - center_x
        dy = player.y + self.state.player_size / 2 - center_y
        distance = math.sqrt(dx * dx + dy * dy)

        return distance > self.state.stage_radius

    async def kill_player(self, player: Player):
        """Kill player and start respawn cooldown"""
        player.is_dead = True
        player.respawn_ready = False
        player.respawn_cooldown = time.time() + self.respawn_cooldown_time
        player.deaths += 1
        player.velocity_x = 0.0
        player.velocity_y = 0.0

        # Add defeat message
        await self.add_message(f"{player.name} がステージから落ちました！")

        update = GameUpdate(type="player_death", data={"player": player.model_dump()})
        await self.broadcast_update(update)

    async def respawn_player(self, player: Player):
        """Respawn player at stage center and reset physics"""
        player.x = self.state.stage_center_x - self.state.player_size / 2
        player.y = self.state.stage_center_y - self.state.player_size / 2
        player.velocity_x = 0.0
        player.velocity_y = 0.0
        player.is_dead = False
        player.respawn_ready = False
        player.respawn_cooldown = 0.0
        player.stamina = player.max_stamina

        # Add respawn message
        await self.add_message(f"{player.name} が復活しました！")

        update = GameUpdate(type="respawn", data={"player": player.model_dump()})
        await self.broadcast_update(update)

    async def broadcast_player_update(self, player: Player):
        update = GameUpdate(type="player_update", data={"player": player.model_dump()})
        await self.broadcast_update(update)

    async def broadcast_all_players_update(self):
        """Broadcast all players state (for physics updates)"""
        players_data = {pid: p.model_dump() for pid, p in self.state.players.items()}
        update = GameUpdate(
            type="game_state",
            data={
                "players": players_data,
                "field_width": self.state.field_width,
                "field_height": self.state.field_height,
                "player_size": self.state.player_size,
                "stage_center_x": self.state.stage_center_x,
                "stage_center_y": self.state.stage_center_y,
                "stage_radius": self.state.stage_radius,
                "messages": self.state.messages,
            },
        )
        await self.broadcast_update(update)

    async def broadcast_update(self, update: GameUpdate):
        if self.connected_clients:
            message = update.model_dump_json()
            dead_connections = []

            for player_id, websocket in self.connected_clients.items():
                try:
                    await websocket.send_text(message)
                except Exception:
                    dead_connections.append(player_id)

            # Clean up dead connections
            for player_id in dead_connections:
                await self.remove_player(player_id)

    async def get_game_state_for_player(self, player_id: str) -> Dict:
        return {
            "type": "game_state",
            "data": {
                "players": {
                    pid: p.model_dump() for pid, p in self.state.players.items()
                },
                "field_width": self.state.field_width,
                "field_height": self.state.field_height,
                "player_size": self.state.player_size,
                "stage_center_x": self.state.stage_center_x,
                "stage_center_y": self.state.stage_center_y,
                "stage_radius": self.state.stage_radius,
                "messages": self.state.messages,
                "your_player_id": player_id,
            },
        }
