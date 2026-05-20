import logging

from application.ports import (
    ChatClientJoinedEvent,
    ChatClientLeftEvent,
    ChatRoomEventListener,
    ChatRoomModifiedEvent,
    ChatRoomRegistry,
    ChatRuntimeStore,
    ChatSessionSavePolicy,
)

from .chat_room_saver import ChatRoomSaver

logger = logging.getLogger(__name__)


class ChatRoomLifecycleHandler(ChatRoomEventListener):
    def __init__(
        self,
        registry: ChatRoomRegistry,
        runtime_store: ChatRuntimeStore,
        saver: ChatRoomSaver,
        save_policy: ChatSessionSavePolicy,
    ) -> None:
        self._registry = registry
        self._runtime_store = runtime_store
        self._saver = saver
        self._save_policy = save_policy

    async def on_client_joined(self, event: ChatClientJoinedEvent) -> None:
        return None

    async def on_client_left(self, event: ChatClientLeftEvent) -> None:
        room = await self._registry.get(event.chat_id)
        if room is None or not room.is_empty:
            return

        try:
            await self._save_policy.on_room_closed(event.chat_id)
            await self._saver.save_if_dirty(event.chat_id)
        except Exception:
            logger.exception("Failed to finalize chat room %s", event.chat_id.value)
        finally:
            await self._runtime_store.clear_room(event.chat_id)
            await self._registry.remove(event.chat_id)

    async def on_room_modified(self, event: ChatRoomModifiedEvent) -> None:
        await self._save_policy.on_room_modified(event.chat_id)
