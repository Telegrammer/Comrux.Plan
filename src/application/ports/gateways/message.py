from typing import Protocol

from domain.entities.message import Message


class MessageCommandGateway(Protocol):
    async def add(self, message: Message) -> None:
        raise NotImplementedError
