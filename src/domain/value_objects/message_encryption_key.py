from dataclasses import dataclass

from domain.exceptions import DomainFieldError


@dataclass(frozen=True)
class MessageEncryptionKey:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise DomainFieldError("Message encryption key cannot be empty")
