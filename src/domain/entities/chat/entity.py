from datetime import datetime

from dataclasses import dataclass, field
from ..base import Entity
from .ids import ChatId
from .context import ContextRef
from .membership import ChatMembership


@dataclass
class Chat(Entity[ChatId]):
    context: ContextRef
    created_at: datetime
    updated_at: datetime
    name: str | None = None
    members: list[ChatMembership] = field(default_factory=list)
