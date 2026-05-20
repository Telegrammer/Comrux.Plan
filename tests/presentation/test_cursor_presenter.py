from datetime import UTC, datetime

import pytest

from presentation.exceptions import InvalidCursorError
from presentation.presenters import ChatHistoryCursor, FernetCursorEncrypter


def test_fernet_cursor_encrypter_roundtrip() -> None:
    encrypter = FernetCursorEncrypter("U6WgwxM_H0F1fvJzDYa0_Ac40mSZ8FGcqqb86QjYgHg=")
    source = ChatHistoryCursor(
        before_created_at=datetime(2026, 4, 12, 10, 30, tzinfo=UTC),
        before_message_id=42,
    )

    token = encrypter.encrypt(source)
    restored = encrypter.decrypt(token)

    assert restored == source


def test_fernet_cursor_encrypter_rejects_invalid_token() -> None:
    encrypter = FernetCursorEncrypter("U6WgwxM_H0F1fvJzDYa0_Ac40mSZ8FGcqqb86QjYgHg=")

    with pytest.raises(InvalidCursorError):
        encrypter.decrypt("invalid-token")
