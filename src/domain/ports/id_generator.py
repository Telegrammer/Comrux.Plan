from typing import Protocol
from domain.value_objects import Id


class IdGenerator[idT: Id](Protocol):
    def __call__(self) -> idT:
        raise NotImplementedError
