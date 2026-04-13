from datetime import datetime

from domain.ports import IdGenerator
from domain.entities.actor import ActorId
from domain.entities.chat import ChatId, Chat, ChatMembership, ContextRef


class ChatIdGenerator(IdGenerator[ChatId]): ...


class ChatService:
    def __init__(self, id_generator: ChatIdGenerator):
        self._id_generator = id_generator

    def create_chat(self, name: str | None, context: ContextRef, now: datetime) -> Chat:
        return Chat(
            id=self._id_generator(),
            name=name,
            context=context,
            created_at=now,
            updated_at=now,
            members=[],
        )

    def create_membership(
        self, chat_id: ChatId, actor_id: ActorId, now: datetime
    ) -> ChatMembership:
        return ChatMembership(chat=chat_id, actor=actor_id, joined_at=now)
