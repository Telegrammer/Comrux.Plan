import asyncio
import time

from application.ports import ChatSessionSavePolicy
from application.services import ChatRoomSaver
from domain.entities.chat import ChatId


class DebounceChatSessionSavePolicy(ChatSessionSavePolicy):
    def __init__(
        self,
        room_saver: ChatRoomSaver,
        delay: float = 5.0,
        check_interval: float = 1.0,
    ) -> None:
        self._room_saver = room_saver
        self._delay = delay
        self._check_interval = check_interval
        self._last_modified: dict[ChatId, float] = {}
        self._watchers: dict[ChatId, asyncio.Task[None]] = {}

    async def start(self) -> None:
        return None

    async def stop(self) -> None:
        for task in self._watchers.values():
            task.cancel()
        if self._watchers:
            await asyncio.gather(*self._watchers.values(), return_exceptions=True)
        self._watchers.clear()
        self._last_modified.clear()

    async def on_room_modified(self, chat_id: ChatId) -> None:
        self._last_modified[chat_id] = time.monotonic()
        if chat_id not in self._watchers:
            self._watchers[chat_id] = asyncio.create_task(self._watch(chat_id))

    async def on_room_closed(self, chat_id: ChatId) -> None:
        self._last_modified.pop(chat_id, None)
        task = self._watchers.pop(chat_id, None)
        if task is not None:
            task.cancel()

    async def _watch(self, chat_id: ChatId) -> None:
        try:
            while True:
                await asyncio.sleep(self._check_interval)
                last_modified = self._last_modified.get(chat_id)
                if last_modified is None:
                    return
                if time.monotonic() - last_modified >= self._delay:
                    await self._room_saver.save_if_dirty(chat_id)
                    self._last_modified.pop(chat_id, None)
                    return
        except asyncio.CancelledError:
            return
        finally:
            self._watchers.pop(chat_id, None)
