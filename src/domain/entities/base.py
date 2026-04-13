from dataclasses import dataclass
from domain.value_objects import Id


@dataclass(eq=False)
class Entity[idT: Id]:
    """Base class for entites

    Attributues:
        id: unqiue identifier that must be in every entity

    Notes:
        Class ensures that entities would be equal not by value but by id

    """

    id: idT

    def __eq__(self, other: object) -> bool:

        if not isinstance(other, Entity):
            return NotImplemented
        if type(self) is not type(other):
            return NotImplemented
        return self.id == other.id
