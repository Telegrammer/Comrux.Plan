from datetime import datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from application.ports import ChatMessage
from application.ports.gateways import (
    DurableMessageCommandGateway,
    MessageCommandGateway,
    MessageQueryGateway,
)
from domain.entities.chat import ChatId
from domain.entities.message import Message, MessageId
from domain.ports import MessageContentEncrypter
from infrastructure.adapters.mappers import (
    SQLAlchemyChatMessageMapper,
    SQLAlchemyDomainMessageMapper,
    SQLAlchemyMessageDTO,
)
from infrastructure.exceptions import network_error_aware
from infrastructure.models import Message as MessageModel
from setup.db_helper import DatabaseHelper


def _dto_to_values(dto: SQLAlchemyMessageDTO) -> dict[str, object]:
    return {
        "runtime_id": dto.runtime_id,
        "content": dto.content,
        "chat_id": dto.chat_id,
        "created_at": dto.created_at,
        "author_id": dto.author_id,
        "author_kind": dto.author_kind,
        "reply_to_message_id": dto.reply_to_message_id,
    }


class SQLAlchemyMessageCommandGateway(MessageCommandGateway, MessageQueryGateway):
    def __init__(
        self,
        session: AsyncSession,
        content_cipher: MessageContentEncrypter,
    ) -> None:
        self._session = session
        self._content_cipher = content_cipher
        self._domain_mapper = SQLAlchemyDomainMessageMapper()
        self._chat_message_mapper = SQLAlchemyChatMessageMapper(content_cipher.decrypt)

    @network_error_aware("Cannot store chat message")
    async def add(self, message: Message) -> None:
        dto = self._domain_mapper.to_dto(message)
        model = MessageModel(
            runtime_id=dto.runtime_id,
            content=dto.content,
            chat_id=dto.chat_id,
            created_at=dto.created_at,
            author_id=dto.author_id,
            author_kind=dto.author_kind,
            reply_to_message_id=dto.reply_to_message_id,
        )
        self._session.add(model)
        await self._session.flush()
        message.id = MessageId(model.id)

    @network_error_aware("Cannot store chat messages")
    async def add_many(self, messages: list[Message]) -> None:
        if not messages:
            return

        stmt = insert(MessageModel).values(
            [_dto_to_values(self._domain_mapper.to_dto(message)) for message in messages]
        )
        await self._session.execute(
            stmt.on_conflict_do_nothing(index_elements=["runtime_id"])
        )
        await self._session.flush()

    @network_error_aware("Cannot load chat message history")
    async def recent_by_chat(
        self,
        chat_id: ChatId,
        limit: int,
        before_created_at: datetime | None = None,
        before_message_id: int | None = None,
    ) -> list[ChatMessage]:
        stmt = select(MessageModel).where(MessageModel.chat_id == chat_id.value)
        if before_created_at is not None and before_message_id is not None:
            stmt = stmt.where(
                or_(
                    MessageModel.created_at < before_created_at,
                    and_(
                        MessageModel.created_at == before_created_at,
                        MessageModel.id < before_message_id,
                    ),
                )
            )

        stmt = (
            stmt.order_by(MessageModel.created_at.desc(), MessageModel.id.desc())
            .limit(limit)
            .options(selectinload(MessageModel.author))
        )
        models = list((await self._session.scalars(stmt)).all())
        models.reverse()
        return [
            self._chat_message_mapper.to_message(
                SQLAlchemyMessageDTO(
                    message_id=model.id,
                    runtime_id=model.runtime_id,
                    content=model.content,
                    chat_id=model.chat_id,
                    created_at=model.created_at,
                    author_id=model.author_id,
                    author_display_name=(
                        model.author.display_name if model.author is not None else None
                    ),
                    author_kind=model.author_kind,
                    reply_to_message_id=model.reply_to_message_id,
                )
            )
            for model in models
        ]


class SQLAlchemyDurableMessageCommandGateway(DurableMessageCommandGateway):
    def __init__(self, db_helper: DatabaseHelper) -> None:
        self._db_helper = db_helper

    @network_error_aware("Cannot persist pending chat messages")
    async def add_many(self, messages: list[Message]) -> None:
        if not messages:
            return

        async with self._db_helper.session_factory() as session:
            stmt = insert(MessageModel).values(
                [
                    _dto_to_values(SQLAlchemyDomainMessageMapper().to_dto(message))
                    for message in messages
                ]
            )
            await session.execute(
                stmt.on_conflict_do_nothing(index_elements=["runtime_id"])
            )
            await session.commit()
