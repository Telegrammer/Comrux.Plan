from sqlalchemy.ext.asyncio import AsyncSession

from application.ports.gateways import MessageCommandGateway
from domain.entities.message import Message, MessageId
from infrastructure.models import Message as MessageModel


class SQLAlchemyMessageCommandGateway(MessageCommandGateway):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, message: Message) -> None:
        model = MessageModel(
            content=message.content,
            chat_id=message.chat_id.value,
            created_at=message.created_at,
            author_id=message.author_id.value if message.author_id else None,
            author_kind=message.author_kind,
            reply_to_message_id=(
                message.reply_to_message_id.value
                if message.reply_to_message_id is not None
                else None
            ),
        )
        self._session.add(model)
        await self._session.flush()
        message.id = MessageId(model.id)
