import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol

from cryptography.fernet import Fernet, InvalidToken

from presentation.exceptions import InvalidCursorError


@dataclass(frozen=True)
class ChatHistoryCursor:
    before_created_at: datetime
    before_message_id: int


class CursorEncrypter(Protocol):
    def encrypt(self, cursor: ChatHistoryCursor) -> str: ...

    def decrypt(self, token: str) -> ChatHistoryCursor: ...


class FernetCursorEncrypter:
    def __init__(self, key: str) -> None:
        self._fernet = Fernet(key.encode("utf-8"))

    def encrypt(self, cursor: ChatHistoryCursor) -> str:
        payload = json.dumps(
            {
                "before_created_at": cursor.before_created_at.isoformat(),
                "before_message_id": cursor.before_message_id,
            }
        )
        token = self._fernet.encrypt(payload.encode("utf-8"))
        return token.decode("utf-8")

    def decrypt(self, token: str) -> ChatHistoryCursor:
        try:
            payload = self._fernet.decrypt(token.encode("utf-8")).decode("utf-8")
            raw: dict[str, Any] = json.loads(payload)
        except (InvalidToken, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise InvalidCursorError("Invalid cursor") from error

        before_created_at = raw.get("before_created_at")
        before_message_id = raw.get("before_message_id")
        if not isinstance(before_created_at, str) or not isinstance(
            before_message_id, int
        ):
            raise InvalidCursorError("Invalid cursor payload")
        try:
            created_at = datetime.fromisoformat(before_created_at)
        except ValueError as error:
            raise InvalidCursorError("Invalid cursor payload") from error

        return ChatHistoryCursor(
            before_created_at=created_at,
            before_message_id=before_message_id,
        )
