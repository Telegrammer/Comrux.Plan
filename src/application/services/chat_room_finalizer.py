from application.ports import ChatRoomRegistry, ChatRuntimeStore, ChatSessionSavePolicy
from domain.entities.chat import ChatId

from .chat_room_saver import ChatRoomSaver


class ChatRoomFinalizer:
    def __init__(
        self,
        saver: ChatRoomSaver,
        registry: ChatRoomRegistry,
        runtime_store: ChatRuntimeStore,
        save_policy: ChatSessionSavePolicy,
    ) -> None:
        self._saver = saver
        self._registry = registry
        self._runtime_store = runtime_store
        self._save_policy = save_policy

    async def finalize(self, chat_id: ChatId) -> None:
        await self._saver.save_if_dirty(chat_id)
        await self._save_policy.on_room_closed(chat_id)
        await self._runtime_store.clear_room(chat_id)
        await self._registry.remove(chat_id)
