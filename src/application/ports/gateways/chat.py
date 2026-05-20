from typing import Protocol

from domain.entities.chat import Chat, ChatId, ContextRef


class ChatCommandGateway(Protocol):
    async def add(self, chat: Chat) -> None:
        raise NotImplementedError


class ChatQueryGateway(Protocol):
    async def by_id(self, chat_id: ChatId) -> Chat | None:
        raise NotImplementedError

    async def by_context(self, context: ContextRef) -> Chat | None:
        raise NotImplementedError
