import asyncio
import weakref

from application.ports import ChatRoomRegistry
from application.ports.gateways import DurableMessageCommandGateway
from domain.entities.chat import ChatId
from domain.services import MessageService


class ChatRoomSaver:
    def __init__(
        self,
        registry: ChatRoomRegistry,
        message_service: MessageService,
        message_commands: DurableMessageCommandGateway,
    ) -> None:
        self._registry = registry
        self._message_service = message_service
        self._message_commands = message_commands
        self._locks: weakref.WeakValueDictionary[str, asyncio.Lock] = (
            weakref.WeakValueDictionary()
        )

    async def save_if_dirty(self, chat_id: ChatId) -> bool:
        lock = self._locks.setdefault(str(chat_id.value), asyncio.Lock())

        async with lock:
            room = await self._registry.get(chat_id)
            if room is None or not room.is_dirty:
                return False

            pending_messages = await room.pending_messages()
            if not pending_messages:
                room.mark_clean()
                return False

            messages = [
                self._message_service.create_user_message(
                    content=item.content,
                    chat_id=item.chat_id,
                    author_id=item.author_id,
                    now=item.created_at,
                    reply_to_message_id=item.reply_to_message_id,
                    runtime_id=item.runtime_id,
                )
                for item in pending_messages
                if item.author_id is not None and item.runtime_id is not None
            ]
            await self._message_commands.add_many(messages)
            await room.mark_persisted(
                [message.runtime_id for message in messages if message.runtime_id is not None]
            )
            room.mark_clean()
            return True
