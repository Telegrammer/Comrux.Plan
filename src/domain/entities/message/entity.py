from dataclasses import dataclass
from datetime import datetime

from ..base import Entity
from ..actor import ActorId
from ..chat import ChatId
from .ids import MessageId
from .enums import MessageAuthorKind


@dataclass
class Message(Entity[MessageId]):
    chat_id: ChatId
    content: bytes
    created_at: datetime
    author_kind: MessageAuthorKind
    author_id: ActorId | None = None
    reply_to_message_id: MessageId | None = None
    runtime_id: str | None = None


@dataclass
class SystemMessage(Message):
    author_kind: MessageAuthorKind = MessageAuthorKind.SYSTEM


@dataclass
class UserMessage(Message):
    author_kind: MessageAuthorKind = MessageAuthorKind.USER
