import json

from redis.asyncio import Redis

from application.ports import ChatMessage, ChatRuntimeStore
from domain.entities.actor import ActorId
from domain.entities.chat import ChatId
from infrastructure.exceptions import network_error_aware

from .mappers import RedisChatMessageDTO, RedisChatMessageMapper


class RedisChatRuntimeStore(ChatRuntimeStore):
    def __init__(
        self,
        redis: Redis,
        mapper: RedisChatMessageMapper,
    ) -> None:
        self._redis = redis
        self._mapper = mapper

    def _pending_order_key(self, chat_id: ChatId) -> str:
        return f"chat:room:{chat_id.value}:pending:order"

    def _pending_payloads_key(self, chat_id: ChatId) -> str:
        return f"chat:room:{chat_id.value}:pending:payloads"

    def _active_members_key(self, chat_id: ChatId) -> str:
        return f"chat:room:{chat_id.value}:members"

    @network_error_aware("Cannot append pending chat message")
    async def append_pending_message(self, message: ChatMessage) -> None:
        dto = self._mapper.to_dto(message)
        payload = json.dumps(dto.__dict__)
        pipeline = self._redis.pipeline(transaction=True)
        pipeline.hset(
            self._pending_payloads_key(message.chat_id),
            dto.runtime_id,
            payload,
        )
        pipeline.rpush(
            self._pending_order_key(message.chat_id),
            dto.runtime_id,
        )
        await pipeline.execute()

    @network_error_aware("Cannot load pending chat messages")
    async def list_pending_messages(self, chat_id: ChatId) -> list[ChatMessage]:
        runtime_ids = await self._redis.lrange(self._pending_order_key(chat_id), 0, -1)
        if not runtime_ids:
            return []

        payloads = await self._redis.hmget(self._pending_payloads_key(chat_id), runtime_ids)
        messages: list[ChatMessage] = []
        for raw_payload in payloads:
            if raw_payload is None:
                continue
            payload = json.loads(raw_payload)
            messages.append(self._mapper.to_message(RedisChatMessageDTO(**payload)))
        return messages

    @network_error_aware("Cannot delete pending chat messages")
    async def delete_pending_messages(
        self, chat_id: ChatId, runtime_ids: list[str]
    ) -> None:
        if not runtime_ids:
            return

        pipeline = self._redis.pipeline(transaction=True)
        for runtime_id in runtime_ids:
            pipeline.lrem(self._pending_order_key(chat_id), 1, runtime_id)
        pipeline.hdel(self._pending_payloads_key(chat_id), *runtime_ids)
        await pipeline.execute()

    @network_error_aware("Cannot add active chat member")
    async def add_active_member(self, chat_id: ChatId, actor_id: ActorId) -> None:
        await self._redis.sadd(self._active_members_key(chat_id), str(actor_id.value))

    @network_error_aware("Cannot remove active chat member")
    async def remove_active_member(self, chat_id: ChatId, actor_id: ActorId) -> None:
        await self._redis.srem(self._active_members_key(chat_id), str(actor_id.value))

    @network_error_aware("Cannot clear chat runtime state")
    async def clear_room(self, chat_id: ChatId) -> None:
        await self._redis.delete(
            self._pending_order_key(chat_id),
            self._pending_payloads_key(chat_id),
            self._active_members_key(chat_id),
        )
