from typing import Protocol

from application.ports import ChatMessage
from domain.entities.message import Message


class DomainMessageMapper[dtoT](Protocol):
    def to_dto(self, domain: Message) -> dtoT:
        raise NotImplementedError

    def to_domain(self, dto: dtoT) -> Message:
        raise NotImplementedError


class ChatMessageMapper[dtoT](Protocol):
    def to_dto(self, message: ChatMessage) -> dtoT:
        raise NotImplementedError

    def to_message(self, dto: dtoT) -> ChatMessage:
        raise NotImplementedError
