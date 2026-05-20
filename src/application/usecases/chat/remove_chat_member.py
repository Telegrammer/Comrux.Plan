from dataclasses import dataclass
from uuid import UUID

from application.exceptions import ActorNotFoundError
from application.ports.gateways import (
    ActorQueryGateway,
    ChatMembershipCommandGateway,
    ChatMembershipQueryGateway,
)
from domain.entities.actor import Actor, ActorId
from domain.entities.chat import ChatId


@dataclass(frozen=True)
class RemoveChatMemberRequest:
    chat_id: ChatId
    actor_id: ActorId

    @classmethod
    def from_primitives(cls, chat_id: UUID, actor_id: str) -> "RemoveChatMemberRequest":
        return cls(chat_id=ChatId(chat_id), actor_id=ActorId(UUID(actor_id)))


@dataclass(frozen=True)
class RemoveChatMemberResponse:
    chat_id: ChatId
    actor_id: ActorId
    display_name: str
    public_id: str
    name: str
    was_removed: bool

    @classmethod
    def from_actor(
        cls, chat_id: ChatId, actor: Actor, was_removed: bool
    ) -> "RemoveChatMemberResponse":
        return cls(
            chat_id=chat_id,
            actor_id=actor.id,
            display_name=actor.display_name.value,
            public_id=actor.public_id,
            name=actor.display_name.value,
            was_removed=was_removed,
        )


class RemoveChatMemberUsecase:
    def __init__(
        self,
        actor_queries: ActorQueryGateway,
        membership_queries: ChatMembershipQueryGateway,
        membership_commands: ChatMembershipCommandGateway,
    ) -> None:
        self._actor_queries = actor_queries
        self._membership_queries = membership_queries
        self._membership_commands = membership_commands

    async def __call__(
        self, request: RemoveChatMemberRequest
    ) -> RemoveChatMemberResponse:
        actor = await self._actor_queries.by_id(request.actor_id)
        if actor is None:
            raise ActorNotFoundError(f"Actor {request.actor_id.value} was not found")

        existing_membership = await self._membership_queries.by_chat_and_actor(
            request.chat_id,
            request.actor_id,
        )
        if existing_membership is None:
            return RemoveChatMemberResponse.from_actor(
                request.chat_id, actor, was_removed=False
            )

        await self._membership_commands.remove(request.chat_id, request.actor_id)
        return RemoveChatMemberResponse.from_actor(request.chat_id, actor, was_removed=True)
