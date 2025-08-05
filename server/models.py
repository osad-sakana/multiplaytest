import random
import uuid
from typing import Dict, Tuple

from pydantic import BaseModel


class Player(BaseModel):
    id: str
    name: str
    x: float
    y: float
    velocity_x: float = 0.0
    velocity_y: float = 0.0
    color: Tuple[int, int, int]
    deaths: int = 0
    stamina: float = 100.0
    max_stamina: float = 100.0
    is_dead: bool = False
    respawn_cooldown: float = 0.0
    respawn_ready: bool = True

    def __init__(self, **data):
        if "id" not in data:
            data["id"] = str(uuid.uuid4())
        if "color" not in data:
            data["color"] = (
                random.randint(50, 255),
                random.randint(50, 255),
                random.randint(50, 255),
            )
        super().__init__(**data)


class GameState(BaseModel):
    players: Dict[str, Player] = {}
    field_width: int = 800
    field_height: int = 600
    player_size: int = 30
    stage_center_x: int = 400
    stage_center_y: int = 300
    stage_radius: int = 250
    messages: list = []


class PlayerInput(BaseModel):
    player_id: str
    action: str  # "move", "boost", "respawn"
    direction: str = None  # "up", "down", "left", "right"


class GameUpdate(BaseModel):
    type: str  # "player_update", "player_joined", "player_left", "respawn", "player_death", "message"
    data: Dict


class GameMessage(BaseModel):
    id: str
    text: str
    timestamp: float
    duration: float = 3.0
