from pydantic import BaseModel
from typing import Dict, List, Tuple
import uuid
import random

class Player(BaseModel):
    id: str
    name: str
    x: float
    y: float
    color: Tuple[int, int, int]
    deaths: int = 0
    is_dashing: bool = False
    dash_cooldown: float = 0.0

    def __init__(self, **data):
        if 'id' not in data:
            data['id'] = str(uuid.uuid4())
        if 'color' not in data:
            data['color'] = (
                random.randint(50, 255),
                random.randint(50, 255),
                random.randint(50, 255)
            )
        super().__init__(**data)

class GameState(BaseModel):
    players: Dict[str, Player] = {}
    field_width: int = 800
    field_height: int = 600
    player_size: int = 30

class PlayerInput(BaseModel):
    player_id: str
    action: str  # "move", "dash"
    direction: str = None  # "up", "down", "left", "right"

class GameUpdate(BaseModel):
    type: str  # "player_update", "player_joined", "player_left", "respawn"
    data: Dict