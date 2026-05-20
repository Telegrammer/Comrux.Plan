from datetime import datetime

from domain.ports import MessageContentEncrypter
from domain.entities.actor import ActorId
from domain.entities.chat import ChatId
from domain.entities.message import MessageId, SystemMessage, UserMessage


class MessageService:
    def __init__(self, encrypter: MessageContentEncrypter):
        self._encrypter = encrypter

    def create_system_message(
        self, content: str, chat_id: ChatId, now: datetime
    ) -> SystemMessage:
        return SystemMessage(
            id=MessageId(None),
            chat_id=chat_id,
            content=self._encrypter(content),
            created_at=now,
        )

    def create_user_message(
        self,
        *,
        content: str,
        chat_id: ChatId,
        author_id: ActorId,
        now: datetime,
        reply_to_message_id: MessageId | None = None,
        runtime_id: str | None = None,
    ) -> UserMessage:
        return UserMessage(
            id=MessageId(None),
            chat_id=chat_id,
            content=self._encrypter(content),
            created_at=now,
            author_id=author_id,
            reply_to_message_id=reply_to_message_id,
            runtime_id=runtime_id,
        )
