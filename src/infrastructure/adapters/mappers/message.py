from dataclasses import dataclass
from datetime import datetime
from typing import Callable
from uuid import UUID

from application.ports import ChatMessage
from application.ports.mappers import ChatMessageMapper, DomainMessageMapper
from domain.entities.actor import ActorId
from domain.entities.chat import ChatId
from domain.entities.message import Message, MessageAuthorKind, MessageId
from utils import ensure_utc_datetime


@dataclass(frozen=True)
class SQLAlchemyMessageDTO:
    content: bytes
    chat_id: UUID
    created_at: datetime
    author_kind: MessageAuthorKind
    runtime_id: str | None = None
    message_id: int | None = None
    author_id: UUID | None = None
    author_display_name: str | None = None
    reply_to_message_id: int | None = None


class SQLAlchemyDomainMessageMapper(DomainMessageMapper[SQLAlchemyMessageDTO]):
    def to_dto(self, domain: Message) -> SQLAlchemyMessageDTO:
        return SQLAlchemyMessageDTO(
            message_id=domain.id.value,
            runtime_id=domain.runtime_id,
            content=domain.content,
            chat_id=domain.chat_id.value,
            created_at=ensure_utc_datetime(domain.created_at),
            author_id=domain.author_id.value if domain.author_id is not None else None,
            author_kind=domain.author_kind,
            reply_to_message_id=(
                domain.reply_to_message_id.value
                if domain.reply_to_message_id is not None
                else None
            ),
        )

    def to_domain(self, dto: SQLAlchemyMessageDTO) -> Message:
        return Message(
            id=MessageId(dto.message_id),
            runtime_id=dto.runtime_id,
            chat_id=ChatId(dto.chat_id),
            content=dto.content,
            created_at=ensure_utc_datetime(dto.created_at),
            author_id=ActorId(dto.author_id) if dto.author_id is not None else None,
            author_kind=dto.author_kind,
            reply_to_message_id=(
                MessageId(dto.reply_to_message_id)
                if dto.reply_to_message_id is not None
                else None
            ),
        )


class SQLAlchemyChatMessageMapper(ChatMessageMapper[SQLAlchemyMessageDTO]):
    def __init__(self, decrypt_content: Callable[[bytes], str]) -> None:
        self._decrypt_content = decrypt_content

    def to_dto(self, message: ChatMessage) -> SQLAlchemyMessageDTO:
        raise NotImplementedError("Chat messages are not written through this mapper")

    def to_message(self, dto: SQLAlchemyMessageDTO) -> ChatMessage:
        return ChatMessage(
            chat_id=ChatId(dto.chat_id),
            content=self._decrypt_content(dto.content),
            created_at=ensure_utc_datetime(dto.created_at),
            author_kind=dto.author_kind,
            runtime_id=dto.runtime_id,
            message_id=MessageId(dto.message_id) if dto.message_id is not None else None,
            author_id=ActorId(dto.author_id) if dto.author_id is not None else None,
            author_display_name=dto.author_display_name,
            reply_to_message_id=(
                MessageId(dto.reply_to_message_id)
                if dto.reply_to_message_id is not None
                else None
            ),
            persisted=True,
        )
