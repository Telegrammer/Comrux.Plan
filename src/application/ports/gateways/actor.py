from typing import Protocol

from domain.entities.actor import Actor, ActorId
from domain.entities.chat import ChatId, ChatMembership


class ActorCommandGateway(Protocol):
    async def add(self, actor: Actor) -> None:
        raise NotImplementedError


class ActorQueryGateway(Protocol):
    async def by_id(self, actor_id: ActorId) -> Actor | None:
        raise NotImplementedError


class ChatMembershipCommandGateway(Protocol):
    async def add(self, membership: ChatMembership) -> None:
        raise NotImplementedError


class ChatMembershipQueryGateway(Protocol):
    async def by_chat_and_actor(
        self, chat_id: ChatId, actor_id: ActorId
    ) -> ChatMembership | None:
        raise NotImplementedError
