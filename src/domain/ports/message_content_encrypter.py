from typing import Protocol


class MessageContentEncrypter(Protocol):
    def __call__(self, content: str) -> bytes:
        raise NotImplementedError
