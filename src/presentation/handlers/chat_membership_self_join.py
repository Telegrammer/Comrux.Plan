from dataclasses import dataclass
from uuid import UUID

from application.compositions import (
    JoinChatMembershipComposition,
    JoinChatMembershipCompositionRequest,
)
from domain.entities.actor import ActorId
from domain.entities.chat import ContextKind, ContextRef
from presentation.exceptions import InvalidAccessTokenError
from presentation.models import ChatMemberJoinedEvent
from presentation.presenters.auth import JwtAccessTokenPresenter


@dataclass(frozen=True)
class JoinChatMembershipRequest:
    token: str
    context_kind: ContextKind
    context_external_id: str


class JoinChatMembershipHandler:
    def __init__(
        self,
        token_presenter: JwtAccessTokenPresenter,
        composition: JoinChatMembershipComposition,
    ) -> None:
        self._token_presenter = token_presenter
        self._composition = composition

    async def __call__(self, request: JoinChatMembershipRequest) -> ChatMemberJoinedEvent:
        auth_info = self._token_presenter.present(request.token)
        try:
            actor_id = ActorId(UUID(auth_info.user_id))
        except ValueError as error:
            raise InvalidAccessTokenError("Token contains invalid user_id") from error

        response = await self._composition(
            JoinChatMembershipCompositionRequest(
                context=ContextRef(
                    kind=request.context_kind,
                    external_id=request.context_external_id,
                ),
                actor_id=actor_id,
            )
        )
        return ChatMemberJoinedEvent(
            chat_id=str(response.chat_id.value),
            chat_was_created=response.chat_was_created,
            member_was_added=response.member_was_added,
        )
