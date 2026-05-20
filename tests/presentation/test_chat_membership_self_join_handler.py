from dataclasses import dataclass
from uuid import UUID

import pytest

from application.compositions import JoinChatMembershipCompositionResponse
from domain.entities.actor import ActorId
from domain.entities.chat import ChatId, ContextKind
from presentation.exceptions import InvalidAccessTokenError
from presentation.handlers import JoinChatMembershipHandler, JoinChatMembershipRequest
from presentation.models import ChatMemberJoinedEvent
from presentation.presenters import AccessAuthInfo


class StubTokenPresenter:
    def __init__(self, user_id: str) -> None:
        self._user_id = user_id

    def present(self, token: str) -> AccessAuthInfo:
        return AccessAuthInfo(key_id="key-1", user_id=self._user_id)


@dataclass
class StubComposition:
    response: JoinChatMembershipCompositionResponse
    requests: list[object]

    async def __call__(self, request: object) -> JoinChatMembershipCompositionResponse:
        self.requests.append(request)
        return self.response


@pytest.mark.asyncio
async def test_join_membership_handler_builds_context_request() -> None:
    actor_id = ActorId(UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
    chat_id = ChatId(UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"))
    composition = StubComposition(
        response=JoinChatMembershipCompositionResponse(
            chat_id=chat_id,
            chat_was_created=True,
            member_was_added=True,
        ),
        requests=[],
    )
    handler = JoinChatMembershipHandler(
        token_presenter=StubTokenPresenter(str(actor_id.value)),
        composition=composition,
    )

    response = await handler(
        JoinChatMembershipRequest(
            token="token",
            context_kind=ContextKind.DOCUMENT,
            context_external_id="doc-1",
        )
    )

    assert isinstance(response, ChatMemberJoinedEvent)
    assert response.chat_id == str(chat_id.value)
    assert response.chat_was_created is True
    assert response.member_was_added is True
    assert len(composition.requests) == 1
    request = composition.requests[0]
    assert request.context.kind is ContextKind.DOCUMENT
    assert request.context.external_id == "doc-1"
    assert request.actor_id == actor_id


@pytest.mark.asyncio
async def test_join_membership_handler_rejects_invalid_user_id_in_token() -> None:
    composition = StubComposition(
        response=JoinChatMembershipCompositionResponse(
            chat_id=ChatId(UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")),
            chat_was_created=False,
            member_was_added=False,
        ),
        requests=[],
    )
    handler = JoinChatMembershipHandler(
        token_presenter=StubTokenPresenter("not-a-uuid"),
        composition=composition,
    )

    with pytest.raises(InvalidAccessTokenError):
        await handler(
            JoinChatMembershipRequest(
                token="token",
                context_kind=ContextKind.DOCUMENT,
                context_external_id="doc-1",
            )
        )
    assert composition.requests == []
