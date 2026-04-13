from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from application.ports.gateways import ChatCommandGateway, ChatQueryGateway
from domain.entities.chat import Chat, ContextRef
from infrastructure.adapters.mappers.chat import ChatDTO, SQLAlchemyChatMapper
from infrastructure.models import Chat as ChatModel


class SQLAlchemyChatCommandGateway(ChatCommandGateway):
    def __init__(self, session: AsyncSession, mapper: SQLAlchemyChatMapper) -> None:
        self._mapper = mapper
        self._session = session

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
