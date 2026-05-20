import asyncio

from application.ports import ChatRoom, ChatRoomRegistry
from domain.entities.chat import ChatId


class InMemoryChatRoomRegistry(ChatRoomRegistry):
    def __init__(self) -> None:
        self._rooms: dict[ChatId, ChatRoom] = {}
        self._locks: dict[ChatId, asyncio.Lock] = {}

    async def get(self, chat_id: ChatId) -> ChatRoom | None:
        return self._rooms.get(chat_id)

    async def register(self, chat_id: ChatId, room: ChatRoom) -> ChatRoom:
        lock = self._locks.setdefault(chat_id, asyncio.Lock())
        async with lock:
            return self._rooms.setdefault(chat_id, room)

    async def remove(self, chat_id: ChatId) -> None:
        self._rooms.pop(chat_id, None)
        self._locks.pop(chat_id, None)

    def get_all(self) -> dict[ChatId, ChatRoom]:
        return dict(self._rooms)
