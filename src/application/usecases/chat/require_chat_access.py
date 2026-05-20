from dataclasses import dataclass

from application.exceptions import (
    ActorNotFoundError,
    ChatMembershipForbiddenError,
    ChatNotFoundError,
)
from application.ports.gateways import (
    ActorQueryGateway,
    ChatMembershipQueryGateway,
    ChatQueryGateway,
)
from domain.entities.actor import Actor, ActorId
from domain.entities.chat import ChatId


@dataclass(frozen=True)
class RequireChatAccessRequest:
    chat_id: ChatId
    actor_id: ActorId


@dataclass(frozen=True)
class RequireChatAccessResponse:
    actor: Actor


class RequireChatAccessUsecase:
    def __init__(
        self,
        actor_queries: ActorQueryGateway,
        chat_queries: ChatQueryGateway,
        membership_queries: ChatMembershipQueryGateway,
    ) -> None:
        self._actor_queries = actor_queries
        self._chat_queries = chat_queries
        self._membership_queries = membership_queries

    async def __call__(
        self, request: RequireChatAccessRequest
    ) -> RequireChatAccessResponse:
        actor = await self._actor_queries.by_id(request.actor_id)
        if actor is None:
            raise ActorNotFoundError(f"Actor {request.actor_id.value} was not found")

        chat = await self._chat_queries.by_id(request.chat_id)
        if chat is None:
            raise ChatNotFoundError(f"Chat {request.chat_id.value} was not found")

        membership = await self._membership_queries.by_chat_and_actor(
            request.chat_id,
            request.actor_id,
        )
        if membership is None:
            raise ChatMembershipForbiddenError(
                f"Actor {request.actor_id.value} is not a member of chat {request.chat_id.value}"
            )

        return RequireChatAccessResponse(actor=actor)
