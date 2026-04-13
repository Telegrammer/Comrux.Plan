from dataclasses import dataclass
from datetime import datetime

from application.ports import Clock
from application.ports.gateways import MessageCommandGateway
from domain.entities.chat import ChatId
from domain.entities.message import MessageId, SystemMessage
from domain.services.message import MessageService


@dataclass(frozen=True)
class CreateSystemMessageRequest:
    chat_id: ChatId
    content: str


@dataclass(frozen=True)
class CreateSystemMessageResponse:
    message_id: MessageId
    created_at: datetime

    @classmethod
    def from_entity(
        cls, message: SystemMessage
    ) -> "CreateSystemMessageResponse":
        return cls(message_id=message.id, created_at=message.created_at)


class CreateSystemMessageUsecase:
    def __init__(
        self,
        clock: Clock,
        message_commands: MessageCommandGateway,
        message_service: MessageService,
    ) -> None:
        self._clock = clock
        self._message_commands = message_commands
        self._message_service = message_service

    async def __call__(
        self, request: CreateSystemMessageRequest
    ) -> CreateSystemMessageResponse:
        message = self._message_service.create_system_message(
            content=request.content,
            chat_id=request.chat_id,
            now=self._clock.now(),
        )
        await self._message_commands.add(message)
        return CreateSystemMessageResponse.from_entity(message)
