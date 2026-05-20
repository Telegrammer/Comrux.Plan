import logging

from application.ports import (
    ChatClientJoinedEvent,
    ChatClientLeftEvent,
    ChatRoomEvent,
    ChatRoomEventListener,
    ChatRoomEventPublisher,
    ChatRoomModifiedEvent,
)
from domain.entities.actor import Actor
from domain.entities.chat import ChatId

logger = logging.getLogger(__name__)


class InMemoryChatRoomEventPublisher(ChatRoomEventPublisher):
    def __init__(self) -> None:
        self._listeners: list[ChatRoomEventListener] = []

    def subscribe(self, listener: ChatRoomEventListener) -> None:
        self._listeners.append(listener)

    async def publish_client_joined(self, chat_id: ChatId, actor: Actor) -> None:
        await self._publish(ChatClientJoinedEvent(chat_id=chat_id, actor=actor))

    async def publish_client_left(self, chat_id: ChatId, actor: Actor) -> None:
        await self._publish(ChatClientLeftEvent(chat_id=chat_id, actor=actor))

    async def publish_room_modified(self, chat_id: ChatId) -> None:
        await self._publish(ChatRoomModifiedEvent(chat_id=chat_id))

    async def _publish(self, event: ChatRoomEvent) -> None:
        for listener in self._listeners:
            try:
                await event.accept(listener)
            except Exception:
                logger.exception(
                    "Listener %s failed for %s",
                    type(listener).__name__,
                    type(event).__name__,
                )
