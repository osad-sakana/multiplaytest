import asyncio
import time
from typing import Dict, Set
from models import Player, GameState, PlayerInput, GameUpdate

class GameManager:
    def __init__(self):
        self.state = GameState()
        self.connected_clients: Dict[str, any] = {}
        self.player_speed = 5.0
        self.dash_speed = 15.0
        self.dash_duration = 0.3
        self.dash_cooldown = 1.0
        
    async def add_player(self, websocket, player_name: str) -> Player:
        spawn_x = self.state.field_width // 2
        spawn_y = self.state.field_height // 2
        
        player = Player(
            name=player_name,
            x=spawn_x,
            y=spawn_y
        )
        
        self.state.players[player.id] = player
        self.connected_clients[player.id] = websocket
        
        # Notify all clients about new player
        update = GameUpdate(
            type="player_joined",
            data={"player": player.dict()}
        )
        await self.broadcast_update(update)
        
        return player
    
    async def remove_player(self, player_id: str):
        if player_id in self.state.players:
            del self.state.players[player_id]
        if player_id in self.connected_clients:
            del self.connected_clients[player_id]
            
        update = GameUpdate(
            type="player_left",
            data={"player_id": player_id}
        )
        await self.broadcast_update(update)
    
    async def handle_player_input(self, player_input: PlayerInput):
        player_id = player_input.player_id
        if player_id not in self.state.players:
            return
            
        player = self.state.players[player_id]
        current_time = time.time()
        
        if player_input.action == "move" and player_input.direction:
            await self.move_player(player, player_input.direction)
        elif player_input.action == "dash" and player_input.direction:
            if player.dash_cooldown <= current_time:
                await self.dash_player(player, player_input.direction, current_time)
    
    async def move_player(self, player: Player, direction: str):
        speed = self.dash_speed if player.is_dashing else self.player_speed
        
        if direction == "up":
            player.y = max(0, player.y - speed)
        elif direction == "down":
            player.y = min(self.state.field_height - self.state.player_size, player.y + speed)
        elif direction == "left":
            player.x = max(0, player.x - speed)
        elif direction == "right":
            player.x = min(self.state.field_width - self.state.player_size, player.x + speed)
        
        # Check if player fell off the field (for dash momentum)
        if self.is_out_of_bounds(player):
            await self.respawn_player(player)
        else:
            await self.broadcast_player_update(player)
    
    async def dash_player(self, player: Player, direction: str, current_time: float):
        player.is_dashing = True
        player.dash_cooldown = current_time + self.dash_cooldown
        
        # Dash movement with higher speed
        dash_distance = self.dash_speed * 3  # Dash covers more distance
        
        if direction == "up":
            player.y = max(-50, player.y - dash_distance)  # Allow going slightly off-screen
        elif direction == "down":
            player.y = min(self.state.field_height + 50, player.y + dash_distance)
        elif direction == "left":
            player.x = max(-50, player.x - dash_distance)
        elif direction == "right":
            player.x = min(self.state.field_width + 50, player.x + dash_distance)
        
        # Schedule dash end
        asyncio.create_task(self.end_dash(player))
        
        if self.is_out_of_bounds(player):
            await self.respawn_player(player)
        else:
            await self.broadcast_player_update(player)
    
    async def end_dash(self, player: Player):
        await asyncio.sleep(self.dash_duration)
        player.is_dashing = False
        await self.broadcast_player_update(player)
    
    def is_out_of_bounds(self, player: Player) -> bool:
        return (player.x < -self.state.player_size or 
                player.x > self.state.field_width or
                player.y < -self.state.player_size or 
                player.y > self.state.field_height)
    
    async def respawn_player(self, player: Player):
        player.x = self.state.field_width // 2
        player.y = self.state.field_height // 2
        player.deaths += 1
        player.is_dashing = False
        
        update = GameUpdate(
            type="respawn",
            data={"player": player.dict()}
        )
        await self.broadcast_update(update)
    
    async def broadcast_player_update(self, player: Player):
        update = GameUpdate(
            type="player_update",
            data={"player": player.dict()}
        )
        await self.broadcast_update(update)
    
    async def broadcast_update(self, update: GameUpdate):
        if self.connected_clients:
            message = update.json()
            dead_connections = []
            
            for player_id, websocket in self.connected_clients.items():
                try:
                    await websocket.send_text(message)
                except:
                    dead_connections.append(player_id)
            
            # Clean up dead connections
            for player_id in dead_connections:
                await self.remove_player(player_id)
    
    async def get_game_state_for_player(self, player_id: str) -> Dict:
        return {
            "type": "game_state",
            "data": {
                "players": {pid: p.dict() for pid, p in self.state.players.items()},
                "field_width": self.state.field_width,
                "field_height": self.state.field_height,
                "player_size": self.state.player_size,
                "your_player_id": player_id
            }
        }