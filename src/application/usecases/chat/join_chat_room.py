from dataclasses import dataclass

from application.ports import ChatMessage, ChatRoom, ChatRoomFactory, ChatRoomRegistry
from application.exceptions import ChatNotFoundError
from application.ports.gateways import ChatQueryGateway
from application.usecases.chat.require_chat_access import (
    RequireChatAccessRequest,
    RequireChatAccessUsecase,
)
from application.usecases.message.get_chat_history import (
    GetChatHistoryRequest,
    GetChatHistoryUsecase,
)
from domain.entities.actor import Actor, ActorId
from domain.entities.chat import ChatId, ContextRef


@dataclass(frozen=True)
class JoinChatRoomRequest:
    context: ContextRef
    actor_id: ActorId
    history_limit: int


@dataclass(frozen=True)
class JoinChatRoomResponse:
    actor: Actor
    room: ChatRoom
    history: list[ChatMessage]


class JoinChatRoomUsecase:
    def __init__(
        self,
        chat_queries: ChatQueryGateway,
        access_usecase: RequireChatAccessUsecase,
        history_usecase: GetChatHistoryUsecase,
        room_registry: ChatRoomRegistry,
        room_factory: ChatRoomFactory,
    ) -> None:
        self._chat_queries = chat_queries
        self._access_usecase = access_usecase
        self._history_usecase = history_usecase
        self._room_registry = room_registry
        self._room_factory = room_factory

    async def __call__(self, request: JoinChatRoomRequest) -> JoinChatRoomResponse:
        chat = await self._chat_queries.by_context(request.context)
        if chat is None:
            raise ChatNotFoundError(
                f"Chat for {request.context.kind.value}:{request.context.external_id} was not found"
            )

        access = await self._access_usecase(
            RequireChatAccessRequest(
                chat_id=chat.id,
                actor_id=request.actor_id,
            )
        )

        active_room = await self._room_registry.get(chat.id)
        if active_room is None:
            active_room = await self._room_registry.register(
                chat.id,
                self._room_factory.create(chat.id),
            )

        history = await self._history_usecase(
            GetChatHistoryRequest(
                chat_id=chat.id,
                limit=request.history_limit,
            )
        )
        return JoinChatRoomResponse(
            actor=access.actor,
            room=active_room,
            history=history.messages,
        )
