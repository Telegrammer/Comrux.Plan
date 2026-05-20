from application.ports import (
    ChatRoom,
    ChatRoomEventPublisher,
    ChatRoomFactory,
    ChatRuntimeStore,
    Clock,
)
from domain.entities.chat import ChatId

from .room import LiveChatRoom


class LiveChatRoomFactory(ChatRoomFactory):
    def __init__(
        self,
        runtime_store: ChatRuntimeStore,
        clock: Clock,
        event_publisher: ChatRoomEventPublisher,
    ) -> None:
        self._runtime_store = runtime_store
        self._clock = clock
        self._event_publisher = event_publisher

    def create(self, chat_id: ChatId) -> ChatRoom:
        return LiveChatRoom(
            chat_id=chat_id,
            runtime_store=self._runtime_store,
            clock=self._clock,
            event_publisher=self._event_publisher,
        )
