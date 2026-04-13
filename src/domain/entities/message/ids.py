from dataclasses import dataclass
from domain.value_objects import Id


@dataclass(frozen=True)
class MessageId(Id[int | None]): ...
