from dataclasses import dataclass
from uuid import UUID

import pytest

from application.compositions import RemoveChatMemberCompositionResponse
from domain.entities.actor import ActorId
from domain.entities.chat import ChatId, ContextKind
from presentation.exceptions import InvalidAccessTokenError
from presentation.handlers import LeaveChatMembershipHandler, LeaveChatMembershipRequest
from presentation.models import ChatMemberLeavedEvent
from presentation.presenters import AccessAuthInfo


class StubTokenPresenter:
    def __init__(self, user_id: str) -> None:
        self._user_id = user_id

    def present(self, token: str) -> AccessAuthInfo:
        return AccessAuthInfo(key_id="key-1", user_id=self._user_id)


@dataclass
class StubComposition:
    response: RemoveChatMemberCompositionResponse
    requests: list[object]

    async def __call__(self, request: object) -> RemoveChatMemberCompositionResponse:
        self.requests.append(request)
        return self.response


@pytest.mark.asyncio
async def test_leave_membership_handler_builds_context_request() -> None:
    actor_id = ActorId(UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
    chat_id = ChatId(UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"))
    composition = StubComposition(
        response=RemoveChatMemberCompositionResponse(
            chat_id=chat_id,
            member_was_removed=True,
            display_name="Alice",
            public_id="alice@example.com",
            name="Alice",
        ),
        requests=[],
    )
    handler = LeaveChatMembershipHandler(
        token_presenter=StubTokenPresenter(str(actor_id.value)),
        composition=composition,
    )

    response = await handler(
        LeaveChatMembershipRequest(
            token="token",
            context_kind=ContextKind.DOCUMENT,
            context_external_id="doc-1",
        )
    )

    assert isinstance(response, ChatMemberLeavedEvent)
    assert response.chat_id == str(chat_id.value)
    assert response.member_was_removed is True
    assert len(composition.requests) == 1
    request = composition.requests[0]
    assert request.context.kind is ContextKind.DOCUMENT
    assert request.context.external_id == "doc-1"
    assert request.actor_id == actor_id


@pytest.mark.asyncio
async def test_leave_membership_handler_rejects_invalid_user_id_in_token() -> None:
    composition = StubComposition(
        response=RemoveChatMemberCompositionResponse(
            chat_id=ChatId(UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")),
            member_was_removed=False,
            display_name="Alice",
            public_id="alice@example.com",
            name="Alice",
        ),
        requests=[],
    )
    handler = LeaveChatMembershipHandler(
        token_presenter=StubTokenPresenter("not-a-uuid"),
        composition=composition,
    )

    with pytest.raises(InvalidAccessTokenError):
        await handler(
            LeaveChatMembershipRequest(
                token="token",
                context_kind=ContextKind.DOCUMENT,
                context_external_id="doc-1",
            )
        )
    assert composition.requests == []
