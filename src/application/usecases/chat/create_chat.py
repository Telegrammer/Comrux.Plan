from dataclasses import dataclass
from datetime import datetime

from application.ports import Clock
from application.ports.gateways import ChatCommandGateway, ChatQueryGateway
from domain.entities.chat import Chat, ChatId, ContextKind, ContextRef
from domain.services.chat import ChatService


@dataclass(frozen=True)
class CreateChatRequest:
    name: str | None
    context: ContextRef

    @classmethod
    def from_primitives(
        cls, name: str | None, context_kind: ContextKind, ref: str
    ) -> "CreateChatRequest":
        return cls(name=name, context=ContextRef(kind=context_kind, external_id=ref))


@dataclass(frozen=True)
class CreateChatResponse:
    chat_id: ChatId
    created_at: datetime
    was_created: bool

    @classmethod
    def from_entity(cls, chat: Chat, was_created: bool) -> "CreateChatResponse":
        return cls(
            chat_id=chat.id,
            created_at=chat.created_at,
            was_created=was_created,
        )


class CreateChatUsecase:
    def __init__(
        self,
        clock: Clock,
        chat_queries: ChatQueryGateway,
        chat_commands: ChatCommandGateway,
        chat_service: ChatService,
    ) -> None:
        self._clock = clock
        self._chat_queries = chat_queries
        self._chat_service = chat_service
        self._chat_commands = chat_commands

    async def __call__(self, request: CreateChatRequest) -> CreateChatResponse:
        existing_chat = await self._chat_queries.by_context(request.context)
        if existing_chat is not None:
            return CreateChatResponse.from_entity(existing_chat, was_created=False)

        now = self._clock.now()
        new_chat = self._chat_service.create_chat(
            name=request.name,
            context=request.context,
            now=now,
        )
        await self._chat_commands.add(new_chat)
        return CreateChatResponse.from_entity(new_chat, was_created=True)
