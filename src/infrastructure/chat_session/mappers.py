from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from application.ports import ChatMessage
from application.ports.mappers import ChatMessageMapper
from domain.entities.actor import ActorId
from domain.entities.chat import ChatId
from domain.entities.message import MessageAuthorKind, MessageId
from utils import ensure_utc_datetime


@dataclass(frozen=True)
class RedisChatMessageDTO:
    runtime_id: str
    chat_id: str
    author_id: str
    author_display_name: str
    content: str
    created_at: str
    author_kind: str
    reply_to_message_id: int | None = None


class RedisChatMessageMapper(ChatMessageMapper[RedisChatMessageDTO]):
    def to_dto(self, message: ChatMessage) -> RedisChatMessageDTO:
        if message.runtime_id is None or message.author_id is None:
            raise ValueError("Runtime chat message requires runtime_id and author_id")

        return RedisChatMessageDTO(
            runtime_id=message.runtime_id,
            chat_id=str(message.chat_id.value),
            author_id=str(message.author_id.value),
            author_display_name=message.author_display_name or "",
            content=message.content,
            created_at=ensure_utc_datetime(message.created_at).isoformat(),
            author_kind=message.author_kind.value,
            reply_to_message_id=(
                message.reply_to_message_id.value
                if message.reply_to_message_id is not None
                else None
            ),
        )

    def to_message(self, dto: RedisChatMessageDTO) -> ChatMessage:
        return ChatMessage(
            chat_id=ChatId(UUID(dto.chat_id)),
            content=dto.content,
            created_at=ensure_utc_datetime(datetime.fromisoformat(dto.created_at)),
            author_kind=MessageAuthorKind(dto.author_kind),
            runtime_id=dto.runtime_id,
            author_id=ActorId(UUID(dto.author_id)),
            author_display_name=dto.author_display_name,
            reply_to_message_id=(
                MessageId(dto.reply_to_message_id)
                if dto.reply_to_message_id is not None
                else None
            ),
            persisted=False,
        )
