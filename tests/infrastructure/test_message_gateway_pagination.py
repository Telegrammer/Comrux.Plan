from datetime import UTC, datetime
from uuid import UUID

import pytest

from domain.entities.chat import ChatId
from infrastructure.adapters.gateways.message import SQLAlchemyMessageCommandGateway


class _FakeCipher:
    def decrypt(self, content: bytes) -> str:
        return content.decode("utf-8")


class _ScalarsResult:
    def __init__(self, models: list[object]) -> None:
        self._models = models

    def all(self) -> list[object]:
        return self._models


class _CapturingSession:
    def __init__(self) -> None:
        self.stmt = None

    async def scalars(self, stmt):
        self.stmt = stmt
        return _ScalarsResult([])


@pytest.mark.asyncio
async def test_recent_by_chat_uses_composite_cursor_filter() -> None:
    session = _CapturingSession()
    gateway = SQLAlchemyMessageCommandGateway(session=session, content_cipher=_FakeCipher())

    await gateway.recent_by_chat(
        chat_id=ChatId(UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")),
        limit=20,
        before_created_at=datetime(2026, 4, 12, 10, 30, tzinfo=UTC),
        before_message_id=123,
    )

    assert session.stmt is not None
    assert len(session.stmt._where_criteria) == 2
    cursor_clause = str(session.stmt._where_criteria[1])
    assert "messages.created_at <" in cursor_clause
    assert "messages.created_at =" in cursor_clause
    assert "messages.id <" in cursor_clause


@pytest.mark.asyncio
async def test_recent_by_chat_without_cursor_has_single_filter() -> None:
    session = _CapturingSession()
    gateway = SQLAlchemyMessageCommandGateway(session=session, content_cipher=_FakeCipher())

    await gateway.recent_by_chat(
        chat_id=ChatId(UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")),
        limit=20,
    )

    assert session.stmt is not None
    assert len(session.stmt._where_criteria) == 1
