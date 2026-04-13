from datetime import UTC, datetime
from uuid import UUID

from domain.entities.chat import ChatId
from domain.entities.message import MessageAuthorKind, MessageId
from domain.services import MessageService


def test_message_service_creates_encrypted_system_message() -> None:
    service = MessageService(encrypter=lambda value: f"encrypted:{value}".encode("utf-8"))

    message = service.create_system_message(
        content="Chat created",
        chat_id=ChatId(UUID("33333333-3333-3333-3333-333333333333")),
        now=datetime(2026, 4, 12, tzinfo=UTC),
    )

    assert message.id == MessageId(None)
    assert message.author_kind is MessageAuthorKind.SYSTEM
    assert message.author_id is None
    assert message.content == b"encrypted:Chat created"
