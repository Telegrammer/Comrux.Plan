from datetime import datetime
from typing import Protocol

from application.ports import ChatMessage
from domain.entities.chat import ChatId
from domain.entities.message import Message


class DurableMessageCommandGateway(Protocol):
    async def add_many(self, messages: list[Message]) -> None:
        raise NotImplementedError


class MessageCommandGateway(Protocol):
    async def add(self, message: Message) -> None:
        raise NotImplementedError

    async def add_many(self, messages: list[Message]) -> None:
        raise NotImplementedError


class MessageQueryGateway(Protocol):
    async def recent_by_chat(
        self,
        chat_id: ChatId,
        limit: int,
        before_created_at: datetime | None = None,
        before_message_id: int | None = None,
    ) -> list[ChatMessage]:
        raise NotImplementedError
