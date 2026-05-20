from datetime import datetime

from pydantic import BaseModel

from application.ports import ChatMessage
from domain.entities.chat import ContextKind


class ChatMembershipContextPayload(BaseModel):
    context_kind: ContextKind
    context_external_id: str


class ChatMessageEvent(BaseModel):
    chat_id: str
    message_id: int | None
    runtime_id: str | None
    author_id: str | None
    author_display_name: str | None
    author_kind: str
    content: str
    created_at: datetime
    reply_to_message_id: int | None
    persisted: bool

    @classmethod
    def from_entity(cls, message: ChatMessage) -> "ChatMessageEvent":
        return cls(
            chat_id=str(message.chat_id.value),
            message_id=message.message_id.value if message.message_id else None,
            runtime_id=message.runtime_id,
            author_id=str(message.author_id.value) if message.author_id else None,
            author_display_name=message.author_display_name,
            author_kind=message.author_kind.value,
            content=message.content,
            created_at=message.created_at,
            reply_to_message_id=(
                message.reply_to_message_id.value
                if message.reply_to_message_id is not None
                else None
            ),
            persisted=message.persisted,
        )


class ChatHistoryEvent(BaseModel):
    messages: list[ChatMessageEvent]
    has_more: bool
    next_cursor: str | None


class ChatMemberLeavedEvent(BaseModel):
    chat_id: str
    member_was_removed: bool


class ChatMemberJoinedEvent(BaseModel):
    chat_id: str
    chat_was_created: bool
    member_was_added: bool
