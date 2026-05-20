import asyncio

from application.ports import ChatRoomRegistry, ChatSessionSavePolicy
from application.services import ChatRoomSaver
from domain.entities.chat import ChatId


class PeriodicChatSessionSavePolicy(ChatSessionSavePolicy):
    def __init__(
        self,
        room_saver: ChatRoomSaver,
        registry: ChatRoomRegistry,
        interval: float = 30.0,
        max_concurrent: int = 20,
    ) -> None:
        self._room_saver = room_saver
        self._registry = registry
        self._interval = interval
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._loop(), name="chat-periodic-save")

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None

    async def on_room_modified(self, chat_id: ChatId) -> None:
        return None

    async def on_room_closed(self, chat_id: ChatId) -> None:
        return None

    async def _loop(self) -> None:
        while True:
            await asyncio.sleep(self._interval)
            await self._save_all_dirty()

    async def _save_all_dirty(self) -> None:
        tasks: list[asyncio.Task[None]] = []
        for chat_id, room in self._registry.get_all().items():
            if not room.is_dirty:
                continue
            tasks.append(asyncio.create_task(self._save_with_limit(chat_id)))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _save_with_limit(self, chat_id: ChatId) -> None:
        async with self._semaphore:
            await self._room_saver.save_if_dirty(chat_id)
