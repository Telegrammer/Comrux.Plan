from application.ports import (
    ChatClientJoinedEvent,
    ChatClientLeftEvent,
    ChatRoomEventListener,
    ChatRoomModifiedEvent,
    ChatRuntimeStore,
)


class ChatRoomPresenceHandler(ChatRoomEventListener):
    def __init__(self, runtime_store: ChatRuntimeStore) -> None:
        self._runtime_store = runtime_store

    async def on_client_joined(self, event: ChatClientJoinedEvent) -> None:
        await self._runtime_store.add_active_member(event.chat_id, event.actor.id)

    async def on_client_left(self, event: ChatClientLeftEvent) -> None:
        await self._runtime_store.remove_active_member(event.chat_id, event.actor.id)

    async def on_room_modified(self, event: ChatRoomModifiedEvent) -> None:
        return None
