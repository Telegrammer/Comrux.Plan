from dataclasses import dataclass


@dataclass(frozen=True, eq=False)
class Id[T]:
    """Base value object for strongly-typed identifiers.

    This class represents an immutable identifier that compares
    by value rather than by object identity.

    It is intended to be subclassed for specific domain entities
    (e.g., UserId, ProjectId) to provide type safety.

    Attributes:
        value: Underlying identifier value.

    Notes:
        Instances are immutable and hashable, allowing their use
        as dictionary keys and set elements.
    """

    value: T

    def __eq__(self, other: object) -> bool:

        if not isinstance(other, Id):
            return NotImplemented
        if type(self) is not type(other):
            return NotImplemented
        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)
