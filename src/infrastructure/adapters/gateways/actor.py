from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from application.ports.gateways import (
    ActorCommandGateway,
    ActorQueryGateway,
    ChatMembershipCommandGateway,
    ChatMembershipQueryGateway,
)
from domain.entities.actor import Actor, ActorId
from domain.entities.chat import ChatId, ChatMembership
from domain.value_objects import Name
from infrastructure.exceptions import network_error_aware
from infrastructure.models import Actor as ActorModel
from infrastructure.models import ChatMembership as ChatMembershipModel


class SQLAlchemyActorCommandGateway(ActorCommandGateway):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @network_error_aware("Cannot store actor")
    async def add(self, actor: Actor) -> None:
        self._session.add(
            ActorModel(
                id=actor.id.value,
                display_name=actor.display_name.value,
                public_id=actor.public_id,
            )
        )
        await self._session.flush()


class SQLAlchemyActorQueryGateway(ActorQueryGateway):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @network_error_aware("Cannot load actor")
    async def by_id(self, actor_id: ActorId) -> Actor | None:
        stmt = select(ActorModel).where(ActorModel.id == actor_id.value)
        model = await self._session.scalar(stmt)
        if model is None:
            return None
        return Actor(
            id=ActorId(model.id),
            display_name=Name(model.display_name),
            public_id=model.public_id,
        )


class SQLAlchemyChatMembershipCommandGateway(ChatMembershipCommandGateway):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @network_error_aware("Cannot store chat membership")
    async def add(self, membership: ChatMembership) -> None:
        self._session.add(
            ChatMembershipModel(
                chat_id=membership.chat.value,
                actor_id=membership.actor.value,
                joined_at=membership.joined_at,
            )
        )
        await self._session.flush()

    @network_error_aware("Cannot delete chat membership")
    async def remove(self, chat_id: ChatId, actor_id: ActorId) -> None:
        stmt = delete(ChatMembershipModel).where(
            ChatMembershipModel.chat_id == chat_id.value,
            ChatMembershipModel.actor_id == actor_id.value,
        )
        await self._session.execute(stmt)
        await self._session.flush()


class SQLAlchemyChatMembershipQueryGateway(ChatMembershipQueryGateway):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @network_error_aware("Cannot load chat membership")
    async def by_chat_and_actor(
        self, chat_id: ChatId, actor_id: ActorId
    ) -> ChatMembership | None:
        stmt = select(ChatMembershipModel).where(
            ChatMembershipModel.chat_id == chat_id.value,
            ChatMembershipModel.actor_id == actor_id.value,
        )
        model = await self._session.scalar(stmt)
        if model is None:
            return None
        return ChatMembership(
            chat=ChatId(model.chat_id),
            actor=ActorId(model.actor_id),
            joined_at=model.joined_at,
        )
