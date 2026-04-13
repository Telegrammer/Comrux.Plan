from dataclasses import dataclass
from datetime import datetime

from .ids import ChatId
from ..actor import ActorId


@dataclass(frozen=True)
class ChatMembership:
    chat: ChatId
    actor: ActorId
    joined_at: datetime
