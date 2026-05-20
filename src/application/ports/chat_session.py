from abc import ABC
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from domain.entities.actor import Actor, ActorId
from domain.entities.chat import ChatId
from domain.entities.message import MessageAuthorKind, MessageId


@dataclass(frozen=True)
class ChatMessage:
    chat_id: ChatId
    content: str
    created_at: datetime
    author_kind: MessageAuthorKind
    runtime_id: str | None = None
    message_id: MessageId | None = None
    author_id: ActorId | None = None
    author_display_name: str | None = None
    reply_to_message_id: MessageId | None = None
    persisted: bool = False


class ChatSessionCommand(ABC): ...


@dataclass(frozen=True)
class PingCommand(ChatSessionCommand): ...


@dataclass(frozen=True)
class SendChatMessageCommand(ChatSessionCommand):
    content: str
    reply_to_message_id: MessageId | None = None


class ChatSessionEvent(ABC): ...


@dataclass(frozen=True)
class PongEvent(ChatSessionEvent): ...


@dataclass(frozen=True)
class ChatHistoryEvent(ChatSessionEvent):
    chat_id: ChatId
    messages: list[ChatMessage]


@dataclass(frozen=True)
class ChatMessageCreatedEvent(ChatSessionEvent):
    message: ChatMessage


@dataclass(frozen=True)
class ChatMemberJoinedEvent(ChatSessionEvent):
    chat_id: ChatId
    actor_id: ActorId
    display_name: str


@dataclass(frozen=True)
class ChatMemberLeftEvent(ChatSessionEvent):
    chat_id: ChatId
    actor_id: ActorId
    display_name: str


@dataclass(frozen=True)
class ChatErrorEvent(ChatSessionEvent):
    code: str
    message: str


class ChatConnection(Protocol):
    async def accept(self) -> None: ...

    async def receive(self) -> ChatSessionCommand: ...

    async def send(self, event: ChatSessionEvent) -> None: ...

    async def close(self) -> None: ...


class ChatRoom(Protocol):
    @property
    def chat_id(self) -> ChatId: ...

    @property
    def is_dirty(self) -> bool: ...

    @property
    def is_empty(self) -> bool: ...

    async def serve(self, actor: Actor, connection: ChatConnection) -> None: ...

    async def pending_messages(self) -> list[ChatMessage]: ...

    async def mark_persisted(self, runtime_ids: list[str]) -> None: ...

    def mark_clean(self) -> None: ...

    async def disconnect_actor(self, actor_id: ActorId) -> int: ...


class ChatRoomFactory(Protocol):
    def create(self, chat_id: ChatId) -> ChatRoom: ...


class ChatRoomRegistry(Protocol):
    async def get(self, chat_id: ChatId) -> ChatRoom | None: ...

    async def register(self, chat_id: ChatId, room: ChatRoom) -> ChatRoom: ...

    async def remove(self, chat_id: ChatId) -> None: ...

    def get_all(self) -> dict[ChatId, ChatRoom]: ...


class ChatRuntimeStore(Protocol):
    async def append_pending_message(self, message: ChatMessage) -> None: ...

    async def list_pending_messages(self, chat_id: ChatId) -> list[ChatMessage]: ...

    async def delete_pending_messages(
        self, chat_id: ChatId, runtime_ids: list[str]
    ) -> None: ...

    async def add_active_member(self, chat_id: ChatId, actor_id: ActorId) -> None: ...

    async def remove_active_member(self, chat_id: ChatId, actor_id: ActorId) -> None: ...

    async def clear_room(self, chat_id: ChatId) -> None: ...


class ChatSessionSavePolicy(Protocol):
    async def start(self) -> None: ...

    async def stop(self) -> None: ...

    async def on_room_modified(self, chat_id: ChatId) -> None: ...

    async def on_room_closed(self, chat_id: ChatId) -> None: ...
