from domain.entities.chat import ChatId
from utils import uuid7


class Uuid7ChatIdGenerator:
    def __call__(self) -> ChatId:
        return ChatId(uuid7())
