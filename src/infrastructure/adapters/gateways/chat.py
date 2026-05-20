from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from application.ports.gateways import ChatCommandGateway, ChatQueryGateway
from domain.entities.chat import Chat, ChatId, ContextRef
from infrastructure.adapters.mappers.chat import ChatDTO, SQLAlchemyChatMapper
from infrastructure.exceptions import network_error_aware
from infrastructure.models import Chat as ChatModel


class SQLAlchemyChatCommandGateway(ChatCommandGateway):
    def __init__(self, session: AsyncSession, mapper: SQLAlchemyChatMapper) -> None:
        self._mapper = mapper
        self._session = session

    @network_error_aware("Cannot store chat")
    async def add(self, chat: Chat) -> None:
        dto = self._mapper.to_dto(chat)
        self._session.add(dto.chat_model)
        for membership in dto.memberships:
            self._session.add(membership)
        await self._session.flush()


class SQLAlchemyChatQueryGateway(ChatQueryGateway):
    def __init__(self, session: AsyncSession, mapper: SQLAlchemyChatMapper) -> None:
        self._mapper = mapper
        self._session = session

    @network_error_aware("Cannot load chat by context")
    async def by_context(self, context: ContextRef) -> Chat | None:
        stmt = (
            select(ChatModel)
            .where(
                ChatModel.context_kind == context.kind.value,
                ChatModel.context_external_id == context.external_id,
            )
            .options(selectinload(ChatModel.members))
        )
        model: ChatModel | None = (
            await self._session.execute(stmt)
        ).scalar_one_or_none()
        if model is None:
            return None
        dto = ChatDTO(chat_model=model, memberships=list(model.members))
        return self._mapper.to_domain(dto)

    @network_error_aware("Cannot load chat by id")
    async def by_id(self, chat_id: ChatId) -> Chat | None:
        stmt = (
            select(ChatModel)
            .where(ChatModel.id == chat_id.value)
            .options(selectinload(ChatModel.members))
        )
        model: ChatModel | None = (
            await self._session.execute(stmt)
        ).scalar_one_or_none()
        if model is None:
            return None
        dto = ChatDTO(chat_model=model, memberships=list(model.members))
        return self._mapper.to_domain(dto)
