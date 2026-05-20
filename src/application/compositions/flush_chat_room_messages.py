from dataclasses import dataclass

from application.ports import ChatMessage, UnitOfWork
from application.ports.gateways import MessageCommandGateway
from domain.services import MessageService


@dataclass(frozen=True)
class FlushChatRoomMessagesRequest:
    messages: list[ChatMessage]


@dataclass(frozen=True)
class FlushChatRoomMessagesResponse:
    persisted_runtime_ids: list[str]


class FlushChatRoomMessagesComposition:
    def __init__(
        self,
        message_commands: MessageCommandGateway,
        message_service: MessageService,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._message_commands = message_commands
        self._message_service = message_service
        self._unit_of_work = unit_of_work

    async def __call__(
        self, request: FlushChatRoomMessagesRequest
    ) -> FlushChatRoomMessagesResponse:
        if not request.messages:
            return FlushChatRoomMessagesResponse(persisted_runtime_ids=[])

        messages = [
            self._message_service.create_user_message(
                content=item.content,
                chat_id=item.chat_id,
                author_id=item.author_id,
                now=item.created_at,
                reply_to_message_id=item.reply_to_message_id,
                runtime_id=item.runtime_id,
            )
            for item in request.messages
        ]

        async with self._unit_of_work:
            await self._message_commands.add_many(messages)

        return FlushChatRoomMessagesResponse(
            persisted_runtime_ids=[item.runtime_id for item in request.messages]
        )
