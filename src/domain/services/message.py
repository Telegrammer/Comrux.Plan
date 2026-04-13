from datetime import datetime

from domain.ports import MessageContentEncrypter
from domain.entities.chat import ChatId
from domain.entities.message import SystemMessage, MessageId


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
