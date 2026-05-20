from dataclasses import dataclass
from uuid import UUID

from application.compositions import (
    RemoveChatMemberComposition,
    RemoveChatMemberCompositionRequest,
)
from domain.entities.actor import ActorId
from domain.entities.chat import ContextKind, ContextRef
from presentation.exceptions import InvalidAccessTokenError
from presentation.models import ChatMemberLeavedEvent
from presentation.presenters.auth import JwtAccessTokenPresenter


@dataclass(frozen=True)
class LeaveChatMembershipRequest:
    token: str
    context_kind: ContextKind
    context_external_id: str


class LeaveChatMembershipHandler:
    def __init__(
        self,
        token_presenter: JwtAccessTokenPresenter,
        composition: RemoveChatMemberComposition,
    ) -> None:
        self._token_presenter = token_presenter
        self._composition = composition

    async def __call__(
        self, request: LeaveChatMembershipRequest
    ) -> ChatMemberLeavedEvent:
        auth_info = self._token_presenter.present(request.token)
        try:
            actor_id = ActorId(UUID(auth_info.user_id))
        except ValueError as error:
            raise InvalidAccessTokenError("Token contains invalid user_id") from error

        response = await self._composition(
            RemoveChatMemberCompositionRequest(
                context=ContextRef(
                    kind=request.context_kind,
                    external_id=request.context_external_id,
                ),
                actor_id=actor_id,
            )
        )
        return ChatMemberLeavedEvent(
            chat_id=str(response.chat_id.value),
            member_was_removed=response.member_was_removed,
        )
