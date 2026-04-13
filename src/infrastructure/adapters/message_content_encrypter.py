from cryptography.fernet import Fernet

from domain.value_objects import MessageEncryptionKey


class FernetMessageContentEncrypter:
    def __init__(self, key: MessageEncryptionKey) -> None:
        self._fernet = Fernet(key.value.encode("utf-8"))

    def __call__(self, content: str) -> bytes:
        return self._fernet.encrypt(content.encode("utf-8"))
