from dataclasses import dataclass

from application.ports import ChatConnection, ChatRoom, ChatRoomEventPublisher
from domain.entities.actor import Actor


@dataclass(frozen=True)
class ServeChatConnectionRequest:
    room: ChatRoom
    actor: Actor
    connection: ChatConnection


class ServeChatConnectionUsecase:
    def __init__(self, events: ChatRoomEventPublisher) -> None:
        self._events = events

    async def __call__(self, request: ServeChatConnectionRequest) -> None:
        await self._events.publish_client_joined(
            request.room.chat_id,
            request.actor,
        )
        try:
            await request.room.serve(request.actor, request.connection)
        finally:
            await self._events.publish_client_left(
                request.room.chat_id,
                request.actor,
            )
