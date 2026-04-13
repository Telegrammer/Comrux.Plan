from typing import Protocol
from domain.entities.chat import Chat


class ChatMapper[dtoT](Protocol):
    def to_dto(self, domain: Chat) -> dtoT:
        raise NotImplementedError

    def to_domain(self, dto: dtoT) -> Chat:
        raise NotImplementedError
