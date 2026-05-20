from dataclasses import dataclass
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID

import pytest

from application.compositions import GetChatHistoryCompositionResponse
from application.ports import ChatMessage
from domain.entities.actor import ActorId
from domain.entities.chat import ChatId
from domain.entities.message import MessageAuthorKind, MessageId
from presentation.handlers import ChatHistoryHandler, GetChatHistoryPageRequest
from presentation.models import ChatMessageEvent
from presentation.presenters import AccessAuthInfo, ChatHistoryCursor


class StubTokenPresenter:
    def present(self, token: str) -> AccessAuthInfo:
        return AccessAuthInfo(
            key_id="key-1",
            user_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        )


@dataclass
class StubCursorEncrypter:
    decrypted: ChatHistoryCursor
    encrypted: str
    decrypt_calls: list[str]
    encrypt_calls: list[ChatHistoryCursor]

    def decrypt(self, token: str) -> ChatHistoryCursor:
        self.decrypt_calls.append(token)
        return self.decrypted

    def encrypt(self, cursor: ChatHistoryCursor) -> str:
        self.encrypt_calls.append(cursor)
        return self.encrypted


class StubComposition:
    def __init__(self, response: GetChatHistoryCompositionResponse) -> None:
        self.response = response
        self.requests = []

    async def __call__(self, request):
        self.requests.append(request)
        return self.response


@pytest.mark.asyncio
async def test_chat_history_handler_uses_cursor_and_builds_next_cursor() -> None:
    chat_id = ChatId(UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"))
    cursor_encrypter = StubCursorEncrypter(
        decrypted=ChatHistoryCursor(
            before_created_at=datetime(2026, 4, 12, 10, 30, tzinfo=UTC),
            before_message_id=9,
        ),
        encrypted="cursor-next",
        decrypt_calls=[],
        encrypt_calls=[],
    )
    composition = StubComposition(
        GetChatHistoryCompositionResponse(
            messages=[
                ChatMessage(
                    chat_id=chat_id,
                    content="hello",
                    created_at=datetime(2026, 4, 12, 10, 0, tzinfo=UTC),
                    author_kind=MessageAuthorKind.USER,
                    message_id=MessageId(11),
                    author_id=ActorId(UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")),
                    author_display_name="Alice",
                    persisted=True,
                )
            ],
            has_more=True,
            next_before_created_at=datetime(2026, 4, 12, 10, 0, tzinfo=UTC),
            next_before_message_id=11,
        )
    )
    handler = ChatHistoryHandler(
        settings=SimpleNamespace(chat_session=SimpleNamespace(history_limit=50)),
        token_presenter=StubTokenPresenter(),
        cursor_encrypter=cursor_encrypter,
        composition=composition,
    )

    response = await handler(
        GetChatHistoryPageRequest(
            token="token",
            chat_id=str(chat_id.value),
            limit=25,
            cursor="cursor-current",
        )
    )

    assert cursor_encrypter.decrypt_calls == ["cursor-current"]
    assert composition.requests
    assert composition.requests[0].before_message_id == 9
    assert composition.requests[0].before_created_at == datetime(
        2026, 4, 12, 10, 30, tzinfo=UTC
    )
    assert response.next_cursor == "cursor-next"
    assert isinstance(response.messages[0], ChatMessageEvent)
    assert cursor_encrypter.encrypt_calls == [
        ChatHistoryCursor(
            before_created_at=datetime(2026, 4, 12, 10, 0, tzinfo=UTC),
            before_message_id=11,
        )
    ]


@pytest.mark.asyncio
async def test_chat_history_handler_clamps_limit_to_settings_value() -> None:
    chat_id = ChatId(UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"))
    composition = StubComposition(
        GetChatHistoryCompositionResponse(
            messages=[],
            has_more=False,
            next_before_created_at=None,
            next_before_message_id=None,
        )
    )
    handler = ChatHistoryHandler(
        settings=SimpleNamespace(chat_session=SimpleNamespace(history_limit=20)),
        token_presenter=StubTokenPresenter(),
        cursor_encrypter=StubCursorEncrypter(
            decrypted=ChatHistoryCursor(
                before_created_at=datetime(2026, 4, 12, 10, 30, tzinfo=UTC),
                before_message_id=9,
            ),
            encrypted="cursor-next",
            decrypt_calls=[],
            encrypt_calls=[],
        ),
        composition=composition,
    )

    await handler(
        GetChatHistoryPageRequest(
            token="token",
            chat_id=str(chat_id.value),
            limit=100,
            cursor=None,
        )
    )

    assert composition.requests
    assert composition.requests[0].limit == 20
