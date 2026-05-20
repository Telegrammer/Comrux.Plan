from dataclasses import dataclass
from datetime import datetime

from application.ports import Clock
from application.ports.gateways import MessageCommandGateway
from domain.entities.actor import ActorId
from domain.entities.chat import ChatId
from domain.entities.message import MessageId, UserMessage
from domain.services.message import MessageService


@dataclass(frozen=True)
class CreateUserMessageRequest:
    chat_id: ChatId
    actor_id: ActorId
    content: str
    created_at: datetime | None = None
    reply_to_message_id: MessageId | None = None
    runtime_id: str | None = None


@dataclass(frozen=True)
class CreateUserMessageResponse:
    message_id: MessageId
    created_at: datetime
    runtime_id: str | None

    @classmethod
    def from_entity(cls, message: UserMessage) -> "CreateUserMessageResponse":
        return cls(
            message_id=message.id,
            created_at=message.created_at,
            runtime_id=message.runtime_id,
        )


class CreateUserMessageUsecase:
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
        self, request: CreateUserMessageRequest
    ) -> CreateUserMessageResponse:
        message = self._message_service.create_user_message(
            content=request.content,
            chat_id=request.chat_id,
            author_id=request.actor_id,
            now=request.created_at or self._clock.now(),
            reply_to_message_id=request.reply_to_message_id,
            runtime_id=request.runtime_id,
        )
        await self._message_commands.add(message)
        return CreateUserMessageResponse.from_entity(message)
