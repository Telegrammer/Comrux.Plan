from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

import pytest

from application.exceptions import ChatMembershipForbiddenError, ChatNotFoundError
from application.ports import ChatMessage, ChatRoom, ChatRoomFactory, ChatRoomRegistry, ChatRuntimeStore
from application.ports.gateways import MessageQueryGateway
from application.usecases.chat.join_chat_room import JoinChatRoomRequest, JoinChatRoomUsecase
from application.usecases.chat.require_chat_access import (
    RequireChatAccessRequest,
    RequireChatAccessUsecase,
)
from application.usecases.message.get_chat_history import (
    GetChatHistoryRequest,
    GetChatHistoryUsecase,
)
from domain.entities.actor import Actor, ActorId
from domain.entities.chat import Chat, ChatId, ChatMembership, ContextKind, ContextRef
from domain.entities.message import MessageAuthorKind, MessageId
from domain.value_objects import Name


class InMemoryActorGateway:
    def __init__(self, existing_actors: list[Actor] | None = None) -> None:
        self._actors_by_id = {actor.id: actor for actor in existing_actors or []}

    async def by_id(self, actor_id: ActorId) -> Actor | None:
        return self._actors_by_id.get(actor_id)


class InMemoryChatGateway:
    def __init__(self, existing_chat: Chat | None = None) -> None:
        self._chat_by_id: dict[ChatId, Chat] = {}
        self._chat_by_context: dict[tuple[str, str], Chat] = {}
        if existing_chat is not None:
            self._chat_by_id[existing_chat.id] = existing_chat
            self._chat_by_context[
                (existing_chat.context.kind.value, existing_chat.context.external_id)
            ] = existing_chat

    async def by_context(self, context: ContextRef) -> Chat | None:
        return self._chat_by_context.get((context.kind.value, context.external_id))

    async def by_id(self, chat_id: ChatId) -> Chat | None:
        return self._chat_by_id.get(chat_id)


class InMemoryMembershipGateway:
    def __init__(self, existing_memberships: list[ChatMembership] | None = None) -> None:
        self._memberships: dict[tuple[ChatId, ActorId], ChatMembership] = {}
        for membership in existing_memberships or []:
            self._memberships[(membership.chat, membership.actor)] = membership

    async def by_chat_and_actor(
        self, chat_id: ChatId, actor_id: ActorId
    ) -> ChatMembership | None:
        return self._memberships.get((chat_id, actor_id))


class StubMessageQueryGateway(MessageQueryGateway):
    def __init__(self, messages: list[ChatMessage]) -> None:
        self._messages = messages

    async def recent_by_chat(
        self,
        chat_id: ChatId,
        limit: int,
        before_created_at: datetime | None = None,
        before_message_id: int | None = None,
    ) -> list[ChatMessage]:
        messages = [message for message in self._messages if message.chat_id == chat_id]
        messages.sort(
            key=lambda message: (
                message.created_at,
                message.message_id.value if message.message_id is not None else 0,
            )
        )
        if before_created_at is not None and before_message_id is not None:
            messages = [
                message
                for message in messages
                if (
                    message.created_at < before_created_at
                    or (
                        message.created_at == before_created_at
                        and message.message_id is not None
                        and message.message_id.value < before_message_id
                    )
                )
            ]
        return messages[-limit:]


class StubRuntimeStore(ChatRuntimeStore):
    def __init__(self, pending_messages: list[ChatMessage] | None = None) -> None:
        self._pending_messages = pending_messages or []

    async def append_pending_message(self, message: ChatMessage) -> None:
        self._pending_messages.append(message)

    async def list_pending_messages(self, chat_id: ChatId) -> list[ChatMessage]:
        return [message for message in self._pending_messages if message.chat_id == chat_id]

    async def delete_pending_messages(self, chat_id: ChatId, runtime_ids: list[str]) -> None:
        self._pending_messages = [
            message
            for message in self._pending_messages
            if message.chat_id != chat_id or message.runtime_id not in runtime_ids
        ]

    async def add_active_member(self, chat_id: ChatId, actor_id: ActorId) -> None:
        return None

    async def remove_active_member(self, chat_id: ChatId, actor_id: ActorId) -> None:
        return None

    async def clear_room(self, chat_id: ChatId) -> None:
        self._pending_messages = [
            message for message in self._pending_messages if message.chat_id != chat_id
        ]


@dataclass
class StubChatRoom:
    chat_id: ChatId
    is_dirty: bool = False
    is_empty: bool = True

    async def serve(self, actor: Actor, connection) -> None:
        return None

    async def pending_messages(self) -> list[ChatMessage]:
        return []

    async def mark_persisted(self, runtime_ids: list[str]) -> None:
        return None

    def mark_clean(self) -> None:
        self.is_dirty = False

    async def disconnect_actor(self, actor_id: ActorId) -> int:
        return 0


class StubChatRoomFactory(ChatRoomFactory):
    def create(self, chat_id: ChatId) -> ChatRoom:
        return StubChatRoom(chat_id=chat_id)


class StubChatRoomRegistry(ChatRoomRegistry):
    def __init__(self) -> None:
        self._rooms: dict[ChatId, ChatRoom] = {}

    async def get(self, chat_id: ChatId) -> ChatRoom | None:
        return self._rooms.get(chat_id)

    async def register(self, chat_id: ChatId, room: ChatRoom) -> ChatRoom:
        self._rooms.setdefault(chat_id, room)
        return self._rooms[chat_id]

    async def remove(self, chat_id: ChatId) -> None:
        self._rooms.pop(chat_id, None)

    def get_all(self) -> dict[ChatId, ChatRoom]:
        return dict(self._rooms)


def build_actor(actor_id: str, display_name: str) -> Actor:
    return Actor(
        id=ActorId(UUID(actor_id)),
        display_name=Name(display_name),
        public_id=f"{display_name.lower()}@example.com",
    )


def build_chat(chat_id: str) -> Chat:
    return Chat(
        id=ChatId(UUID(chat_id)),
        name=None,
        context=ContextRef(kind=ContextKind.PROJECT, external_id="project-1"),
        created_at=datetime(2026, 4, 12, tzinfo=UTC),
        updated_at=datetime(2026, 4, 12, tzinfo=UTC),
        members=[],
    )


@pytest.mark.asyncio
async def test_require_chat_access_rejects_non_member() -> None:
    actor = build_actor("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "Alice")
    chat = build_chat("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
    usecase = RequireChatAccessUsecase(
        actor_queries=InMemoryActorGateway(existing_actors=[actor]),
        chat_queries=InMemoryChatGateway(existing_chat=chat),
        membership_queries=InMemoryMembershipGateway(),
    )

    with pytest.raises(ChatMembershipForbiddenError):
        await usecase(
            RequireChatAccessRequest(
                chat_id=chat.id,
                actor_id=actor.id,
            )
        )


@pytest.mark.asyncio
async def test_require_chat_access_rejects_missing_chat() -> None:
    actor = build_actor("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "Alice")
    usecase = RequireChatAccessUsecase(
        actor_queries=InMemoryActorGateway(existing_actors=[actor]),
        chat_queries=InMemoryChatGateway(),
        membership_queries=InMemoryMembershipGateway(),
    )

    with pytest.raises(ChatNotFoundError):
        await usecase(
            RequireChatAccessRequest(
                chat_id=ChatId(UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")),
                actor_id=actor.id,
            )
        )


@pytest.mark.asyncio
async def test_get_chat_history_merges_persisted_and_pending_messages() -> None:
    chat_id = ChatId(UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"))
    actor_id = ActorId(UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
    usecase = GetChatHistoryUsecase(
        message_queries=StubMessageQueryGateway(
            [
                ChatMessage(
                    chat_id=chat_id,
                    content="persisted",
                    created_at=datetime(2026, 4, 12, 10, 0, tzinfo=UTC),
                    author_kind=MessageAuthorKind.USER,
                    message_id=MessageId(1),
                    author_id=actor_id,
                    author_display_name="Alice",
                    persisted=True,
                )
            ]
        ),
        runtime_store=StubRuntimeStore(
            [
                ChatMessage(
                    chat_id=chat_id,
                    content="pending",
                    created_at=datetime(2026, 4, 12, 10, 1, tzinfo=UTC),
                    author_kind=MessageAuthorKind.USER,
                    runtime_id="runtime-1",
                    author_id=actor_id,
                    author_display_name="Alice",
                    persisted=False,
                )
            ]
        ),
    )

    response = await usecase(GetChatHistoryRequest(chat_id=chat_id, limit=10))

    assert [message.content for message in response.messages] == ["persisted", "pending"]
    assert [message.persisted for message in response.messages] == [True, False]
    assert response.has_more is False
    assert response.next_before_created_at is None
    assert response.next_before_message_id is None


@pytest.mark.asyncio
async def test_get_chat_history_with_cursor_excludes_pending_messages() -> None:
    chat_id = ChatId(UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"))
    actor_id = ActorId(UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
    usecase = GetChatHistoryUsecase(
        message_queries=StubMessageQueryGateway(
            [
                ChatMessage(
                    chat_id=chat_id,
                    content=f"persisted-{index}",
                    created_at=datetime(2026, 4, 12, 10, index, tzinfo=UTC),
                    author_kind=MessageAuthorKind.USER,
                    message_id=MessageId(index),
                    author_id=actor_id,
                    author_display_name="Alice",
                    persisted=True,
                )
                for index in range(1, 6)
            ]
        ),
        runtime_store=StubRuntimeStore(
            [
                ChatMessage(
                    chat_id=chat_id,
                    content="pending",
                    created_at=datetime(2026, 4, 12, 11, 0, tzinfo=UTC),
                    author_kind=MessageAuthorKind.USER,
                    runtime_id="runtime-1",
                    author_id=actor_id,
                    author_display_name="Alice",
                    persisted=False,
                )
            ]
        ),
    )

    response = await usecase(
        GetChatHistoryRequest(
            chat_id=chat_id,
            limit=2,
            before_created_at=datetime(2026, 4, 12, 10, 5, tzinfo=UTC),
            before_message_id=5,
        )
    )

    assert [message.content for message in response.messages] == [
        "persisted-3",
        "persisted-4",
    ]
    assert all(message.persisted for message in response.messages)
    assert response.has_more is True
    assert response.next_before_message_id == 3
    assert response.next_before_created_at == datetime(2026, 4, 12, 10, 3, tzinfo=UTC)


@pytest.mark.asyncio
async def test_join_chat_room_returns_existing_room_and_history() -> None:
    actor = build_actor("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "Alice")
    chat = build_chat("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
    membership = ChatMembership(
        chat=chat.id,
        actor=actor.id,
        joined_at=datetime(2026, 4, 12, tzinfo=UTC),
    )
    registry = StubChatRoomRegistry()
    existing_room = StubChatRoom(chat_id=chat.id)
    await registry.register(chat.id, existing_room)
    usecase = JoinChatRoomUsecase(
        chat_queries=InMemoryChatGateway(existing_chat=chat),
        access_usecase=RequireChatAccessUsecase(
            actor_queries=InMemoryActorGateway(existing_actors=[actor]),
            chat_queries=InMemoryChatGateway(existing_chat=chat),
            membership_queries=InMemoryMembershipGateway(
                existing_memberships=[membership]
            ),
        ),
        history_usecase=GetChatHistoryUsecase(
            message_queries=StubMessageQueryGateway([]),
            runtime_store=StubRuntimeStore(),
        ),
        room_registry=registry,
        room_factory=StubChatRoomFactory(),
    )

    response = await usecase(
        JoinChatRoomRequest(
            context=chat.context,
            actor_id=actor.id,
            history_limit=20,
        )
    )

    assert response.room is existing_room
    assert response.actor.id == actor.id
    assert response.history == []
