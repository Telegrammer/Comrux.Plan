from dataclasses import dataclass
from domain.value_objects import Name
from ..base import Entity
from .ids import ActorId


@dataclass
class Actor(Entity[ActorId]):
    display_name: Name
    public_id: str
