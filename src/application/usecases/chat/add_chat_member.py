from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from application.exceptions import ActorNotFoundError
from application.ports import Clock
from application.ports.gateways import (
    ActorQueryGateway,
    ChatMembershipCommandGateway,
    ChatMembershipQueryGateway,
)
from domain.entities.actor import Actor, ActorId
from domain.entities.chat import ChatId, ChatMembership
from domain.services import ChatService


@dataclass(frozen=True)
class AddChatMemberRequest:
    chat_id: ChatId
    actor_id: ActorId

    @classmethod
    def from_primitives(cls, chat_id: UUID, actor_id: str) -> "AddChatMemberRequest":
        return cls(chat_id=ChatId(chat_id), actor_id=ActorId(UUID(actor_id)))


@dataclass(frozen=True)
class AddChatMemberResponse:
    chat_id: ChatId
    actor_id: ActorId
    joined_at: datetime
    display_name: str
    public_id: str
    was_added: bool

    @classmethod
    def from_entity(
        cls, membership: ChatMembership, actor: Actor, was_added: bool
    ) -> "AddChatMemberResponse":
        return cls(
            chat_id=membership.chat,
            actor_id=membership.actor,
            joined_at=membership.joined_at,
            display_name=actor.display_name.value,
            public_id=actor.public_id,
            was_added=was_added,
        )


class AddChatMemberUsecase:
    def __init__(
        self,
        clock: Clock,
        actor_queries: ActorQueryGateway,
        membership_queries: ChatMembershipQueryGateway,
        membership_commands: ChatMembershipCommandGateway,
        chat_service: ChatService,
    ) -> None:
        self._clock = clock
        self._actor_queries = actor_queries
        self._membership_queries = membership_queries
        self._membership_commands = membership_commands
        self._chat_service = chat_service

    async def __call__(self, request: AddChatMemberRequest) -> AddChatMemberResponse:
        actor = await self._actor_queries.by_id(request.actor_id)
        if actor is None:
            raise ActorNotFoundError(f"Actor {request.actor_id.value} was not found")

        existing_membership = await self._membership_queries.by_chat_and_actor(
            request.chat_id,
            request.actor_id,
        )
        if existing_membership is not None:
            return AddChatMemberResponse.from_entity(
                existing_membership, actor=actor, was_added=False
            )

        membership = self._chat_service.create_membership(
            chat_id=request.chat_id,
            actor_id=request.actor_id,
            now=self._clock.now(),
        )
        await self._membership_commands.add(membership)
        return AddChatMemberResponse.from_entity(membership, actor=actor, was_added=True)
