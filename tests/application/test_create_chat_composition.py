from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Callable
from uuid import UUID

import pytest

from application.compositions import CreateChatComposition
from application.ports import Clock
from application.ports.gateways import (
    ChatCommandGateway,
    ChatQueryGateway,
    MessageCommandGateway,
)
from application.usecases import (
    CreateChatRequest,
    CreateChatUsecase,
    CreateSystemMessageUsecase,
)
from domain.entities.chat import Chat, ChatId, ContextKind, ContextRef
from domain.entities.message import Message, MessageAuthorKind
from domain.services import ChatService, MessageService
from infrastructure.adapters.unit_of_work import UnitOfWorkImpl


class FixedClock(Clock):
    def __init__(self, now_value: datetime) -> None:
        self._now_value = now_value

    def now(self) -> datetime:
        return self._now_value


class InMemoryChatGateway(ChatCommandGateway, ChatQueryGateway):
    def __init__(self, existing_chat: Chat | None = None) -> None:
        self.saved_chats: list[Chat] = []
        self._chat_by_context: dict[tuple[str, str], Chat] = {}
        if existing_chat is not None:
            self._chat_by_context[
                (existing_chat.context.kind.value, existing_chat.context.external_id)
            ] = existing_chat

    async def add(self, chat: Chat) -> None:
        self.saved_chats.append(chat)
        self._chat_by_context[(chat.context.kind.value, chat.context.external_id)] = chat

    async def by_context(self, context: ContextRef) -> Chat | None:
        return self._chat_by_context.get((context.kind.value, context.external_id))


class InMemoryMessageGateway(MessageCommandGateway):
    def __init__(self) -> None:
        self.saved_messages: list[Message] = []

    async def add(self, message: Message) -> None:
        self.saved_messages.append(message)


@dataclass(frozen=True)
class Scenario:
    composition: CreateChatComposition
    chat_gateway: InMemoryChatGateway
    message_gateway: InMemoryMessageGateway


def build_scenario(
    *,
    existing_chat: Chat | None = None,
    encrypted_message: Callable[[str], bytes] | None = None,
) -> Scenario:
    chat_gateway = InMemoryChatGateway(existing_chat=existing_chat)
    message_gateway = InMemoryMessageGateway()
    fixed_clock = FixedClock(datetime(2026, 4, 12, tzinfo=UTC))
    chat_service = ChatService(
        id_generator=lambda: ChatId(UUID("11111111-1111-1111-1111-111111111111"))
    )
    message_service = MessageService(
        encrypter=encrypted_message or (lambda value: f"enc:{value}".encode("utf-8"))
    )
    create_chat_usecase = CreateChatUsecase(
        clock=fixed_clock,
        chat_queries=chat_gateway,
        chat_commands=chat_gateway,
        chat_service=chat_service,
    )
    create_system_message_usecase = CreateSystemMessageUsecase(
        clock=fixed_clock,
        message_commands=message_gateway,
        message_service=message_service,
    )
    composition = CreateChatComposition(
        create_chat=create_chat_usecase,
        create_system_message=create_system_message_usecase,
        unit_of_work=UnitOfWorkImpl(),
    )
    return Scenario(
        composition=composition,
        chat_gateway=chat_gateway,
        message_gateway=message_gateway,
    )


@pytest.mark.asyncio
async def test_create_chat_composition_creates_chat_and_system_message() -> None:
    scenario = build_scenario()
    request = CreateChatRequest.from_primitives(
        name=None,
        context_kind=ContextKind.PROJECT,
        ref="project-1",
    )

    response = await scenario.composition(request)

    assert response.was_created is True
    assert response.chat_id.value == UUID("11111111-1111-1111-1111-111111111111")
    assert len(scenario.chat_gateway.saved_chats) == 1
    assert len(scenario.message_gateway.saved_messages) == 1
    assert scenario.message_gateway.saved_messages[0].author_kind is MessageAuthorKind.SYSTEM
    assert scenario.message_gateway.saved_messages[0].content == b"enc:Chat created"


@pytest.mark.asyncio
async def test_create_chat_composition_is_idempotent_for_existing_context() -> None:
    existing_chat = Chat(
        id=ChatId(UUID("22222222-2222-2222-2222-222222222222")),
        name=None,
        context=ContextRef(kind=ContextKind.DOCUMENT, external_id="document-7"),
        created_at=datetime(2026, 4, 10, tzinfo=UTC),
        updated_at=datetime(2026, 4, 10, tzinfo=UTC),
        members=[],
    )
    scenario = build_scenario(existing_chat=existing_chat)
    request = CreateChatRequest.from_primitives(
        name=None,
        context_kind=ContextKind.DOCUMENT,
        ref="document-7",
    )

    response = await scenario.composition(request)

    assert response.was_created is False
    assert response.chat_id == existing_chat.id
    assert scenario.chat_gateway.saved_chats == []
    assert scenario.message_gateway.saved_messages == []
