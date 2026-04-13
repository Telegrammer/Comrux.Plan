from dataclasses import dataclass
from domain.value_objects import Id
from uuid import UUID


@dataclass(frozen=True)
class ChatId(Id[UUID]): ...
