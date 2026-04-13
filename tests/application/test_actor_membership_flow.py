from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

import pytest

from application.compositions.add_project_member import (
    AddProjectMemberComposition,
    AddProjectMemberRequest,
)
from application.compositions.create_project_chat import (
    CreateProjectChatComposition,
    CreateProjectChatRequest,
)
from application.ports import Clock
from application.ports.gateways import (
    ActorCommandGateway,
    ActorQueryGateway,
    ChatCommandGateway,
    ChatMembershipCommandGateway,
    ChatMembershipQueryGateway,
    ChatQueryGateway,
    MessageCommandGateway,
)
from application.usecases import (
    AddChatMemberUsecase,
    CreateActorRequest,
    CreateActorUsecase,
    CreateChatRequest,
    CreateChatUsecase,
    CreateSystemMessageUsecase,
)
from domain.entities.actor import Actor, ActorId
from domain.entities.chat import Chat, ChatId, ChatMembership, ContextKind, ContextRef
from domain.entities.message import Message
from domain.services import ActorService, ChatService, MessageService
from infrastructure.adapters.unit_of_work import UnitOfWorkImpl


class FixedClock(Clock):
    def __init__(self, now_value: datetime) -> None:
        self._now_value = now_value

    def now(self) -> datetime:
        return self._now_value


class InMemoryActorGateway(ActorCommandGateway, ActorQueryGateway):
    def __init__(self, existing_actors: list[Actor] | None = None) -> None:
        self.saved_actors: list[Actor] = []
        self._actors_by_id: dict[ActorId, Actor] = {}
        for actor in existing_actors or []:
            self._actors_by_id[actor.id] = actor

    async def add(self, actor: Actor) -> None:
        self.saved_actors.append(actor)
        self._actors_by_id[actor.id] = actor

    async def by_id(self, actor_id: ActorId) -> Actor | None:
        return self._actors_by_id.get(actor_id)


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


class InMemoryMembershipGateway(
    ChatMembershipCommandGateway, ChatMembershipQueryGateway
):
    def __init__(self, existing_memberships: list[ChatMembership] | None = None) -> None:
        self.saved_memberships: list[ChatMembership] = []
        self._memberships: dict[tuple[ChatId, ActorId], ChatMembership] = {}
        for membership in existing_memberships or []:
            self._memberships[(membership.chat, membership.actor)] = membership

    async def add(self, membership: ChatMembership) -> None:
        self.saved_memberships.append(membership)
        self._memberships[(membership.chat, membership.actor)] = membership

    async def by_chat_and_actor(
        self, chat_id: ChatId, actor_id: ActorId
    ) -> ChatMembership | None:
        return self._memberships.get((chat_id, actor_id))


class InMemoryMessageGateway(MessageCommandGateway):
    def __init__(self) -> None:
        self.saved_messages: list[Message] = []

    async def add(self, message: Message) -> None:
        self.saved_messages.append(message)


@dataclass(frozen=True)
class FlowScenario:
    actor_gateway: InMemoryActorGateway
    chat_gateway: InMemoryChatGateway
    membership_gateway: InMemoryMembershipGateway
    message_gateway: InMemoryMessageGateway
    create_actor_usecase: CreateActorUsecase
    create_project_chat: CreateProjectChatComposition
    add_project_member: AddProjectMemberComposition


def build_actor(actor_id: str, display_name: str, *, email: str) -> Actor:
    return ActorService().create_actor(
        actor_id=ActorId(UUID(actor_id)),
        display_name=display_name,
        public_id=email,
    )


def build_flow_scenario(
    *,
    existing_actors: list[Actor] | None = None,
    existing_chat: Chat | None = None,
    existing_memberships: list[ChatMembership] | None = None,
) -> FlowScenario:
    actor_gateway = InMemoryActorGateway(existing_actors=existing_actors)
    chat_gateway = InMemoryChatGateway(existing_chat=existing_chat)
    membership_gateway = InMemoryMembershipGateway(
        existing_memberships=existing_memberships
    )
    message_gateway = InMemoryMessageGateway()
    fixed_clock = FixedClock(datetime(2026, 4, 12, tzinfo=UTC))

    create_chat_usecase = CreateChatUsecase(
        clock=fixed_clock,
        chat_queries=chat_gateway,
        chat_commands=chat_gateway,
        chat_service=ChatService(
            id_generator=lambda: ChatId(UUID("11111111-1111-1111-1111-111111111111"))
        ),
    )
    add_chat_member_usecase = AddChatMemberUsecase(
        clock=fixed_clock,
        actor_queries=actor_gateway,
        membership_queries=membership_gateway,
        membership_commands=membership_gateway,
        chat_service=ChatService(
            id_generator=lambda: ChatId(UUID("11111111-1111-1111-1111-111111111111"))
        ),
    )
    create_system_message_usecase = CreateSystemMessageUsecase(
        clock=fixed_clock,
        message_commands=message_gateway,
        message_service=MessageService(
            encrypter=lambda value: f"enc:{value}".encode("utf-8")
        ),
    )

    return FlowScenario(
        actor_gateway=actor_gateway,
        chat_gateway=chat_gateway,
        membership_gateway=membership_gateway,
        message_gateway=message_gateway,
        create_actor_usecase=CreateActorUsecase(
            actor_queries=actor_gateway,
            actor_commands=actor_gateway,
            actor_service=ActorService(),
        ),
        create_project_chat=CreateProjectChatComposition(
            create_chat=create_chat_usecase,
            add_chat_member=add_chat_member_usecase,
            create_system_message=create_system_message_usecase,
            unit_of_work=UnitOfWorkImpl(),
        ),
        add_project_member=AddProjectMemberComposition(
            create_chat=create_chat_usecase,
            add_chat_member=add_chat_member_usecase,
            create_system_message=create_system_message_usecase,
            unit_of_work=UnitOfWorkImpl(),
        ),
    )


@pytest.mark.asyncio
async def test_create_actor_usecase_creates_actor_once() -> None:
    scenario = build_flow_scenario()
    request = CreateActorRequest.from_primitives(
        actor_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        display_name="Alice",
        email="alice@example.com",
    )

    response = await scenario.create_actor_usecase(request)

    assert response.was_created is True
    assert len(scenario.actor_gateway.saved_actors) == 1
    assert scenario.actor_gateway.saved_actors[0].public_id == "alice@example.com"


@pytest.mark.asyncio
async def test_create_project_chat_adds_owner_and_chat_created_message() -> None:
    owner = build_actor(
        "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "Alice",
        email="alice@example.com",
    )
    scenario = build_flow_scenario(existing_actors=[owner])
    request = CreateProjectChatRequest(
        chat=CreateChatRequest.from_primitives(
            name=None,
            context_kind=ContextKind.PROJECT,
            ref="project-1",
        ),
        owner_id=owner.id,
    )

    response = await scenario.create_project_chat(request)

    assert response.chat_was_created is True
    assert response.owner_was_added is True
    assert len(scenario.chat_gateway.saved_chats) == 1
    assert len(scenario.membership_gateway.saved_memberships) == 1
    assert [message.content for message in scenario.message_gateway.saved_messages] == [
        b"enc:Chat created"
    ]


@pytest.mark.asyncio
async def test_add_project_member_creates_missing_chat_and_member_message() -> None:
    member = build_actor(
        "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        "Bob",
        email="bob@example.com",
    )
    scenario = build_flow_scenario(existing_actors=[member])
    request = AddProjectMemberRequest(
        chat=CreateChatRequest.from_primitives(
            name=None,
            context_kind=ContextKind.PROJECT,
            ref="project-2",
        ),
        actor_id=member.id,
    )

    response = await scenario.add_project_member(request)

    assert response.chat_was_created is True
    assert response.member_was_added is True
    assert len(scenario.chat_gateway.saved_chats) == 1
    assert len(scenario.membership_gateway.saved_memberships) == 1
    assert [message.content for message in scenario.message_gateway.saved_messages] == [
        b"enc:Chat created",
        b"enc:Member added",
    ]


@pytest.mark.asyncio
async def test_add_project_member_is_idempotent_for_existing_membership() -> None:
    member = build_actor(
        "cccccccc-cccc-cccc-cccc-cccccccccccc",
        "Carol",
        email="carol@example.com",
    )
    existing_chat = Chat(
        id=ChatId(UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")),
        name=None,
        context=ContextRef(kind=ContextKind.PROJECT, external_id="project-3"),
        created_at=datetime(2026, 4, 10, tzinfo=UTC),
        updated_at=datetime(2026, 4, 10, tzinfo=UTC),
        members=[],
    )
    existing_membership = ChatMembership(
        chat=existing_chat.id,
        actor=member.id,
        joined_at=datetime(2026, 4, 10, tzinfo=UTC),
    )
    scenario = build_flow_scenario(
        existing_actors=[member],
        existing_chat=existing_chat,
        existing_memberships=[existing_membership],
    )
    request = AddProjectMemberRequest(
        chat=CreateChatRequest.from_primitives(
            name=None,
            context_kind=ContextKind.PROJECT,
            ref="project-3",
        ),
        actor_id=member.id,
    )

    response = await scenario.add_project_member(request)

    assert response.chat_was_created is False
    assert response.member_was_added is False
    assert scenario.chat_gateway.saved_chats == []
    assert scenario.membership_gateway.saved_memberships == []
    assert scenario.message_gateway.saved_messages == []
