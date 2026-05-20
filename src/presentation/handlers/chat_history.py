from dataclasses import dataclass
from uuid import UUID

from application.compositions import (
    GetChatHistoryComposition,
    GetChatHistoryCompositionRequest,
)
from domain.entities.actor import ActorId
from domain.entities.chat import ChatId
from presentation.exceptions import InvalidAccessTokenError
from presentation.models import ChatHistoryEvent, ChatMessageEvent
from presentation.presenters import ChatHistoryCursor, CursorEncrypter, JwtAccessTokenPresenter
from setup.config import Settings


@dataclass(frozen=True)
class GetChatHistoryPageRequest:
    token: str
    chat_id: str
    limit: int
    cursor: str | None = None


class ChatHistoryHandler:
    def __init__(
        self,
        settings: Settings,
        token_presenter: JwtAccessTokenPresenter,
        cursor_encrypter: CursorEncrypter,
        composition: GetChatHistoryComposition,
    ) -> None:
        self._settings = settings
        self._token_presenter = token_presenter
        self._cursor_encrypter = cursor_encrypter
        self._composition = composition

    async def __call__(
        self, request: GetChatHistoryPageRequest
    ) -> ChatHistoryEvent:
        auth_info = self._token_presenter.present(request.token)
        try:
            actor_id = ActorId(UUID(auth_info.user_id))
        except ValueError as error:
            raise InvalidAccessTokenError("Token contains invalid user_id") from error

        try:
            chat_id = ChatId(UUID(request.chat_id))
        except ValueError as error:
            raise InvalidAccessTokenError("Chat id is invalid") from error

        before_cursor: ChatHistoryCursor | None = None
        if request.cursor is not None:
            before_cursor = self._cursor_encrypter.decrypt(request.cursor)

        limit = min(max(request.limit, 1), self._settings.chat_session.history_limit)
        response = await self._composition(
            GetChatHistoryCompositionRequest(
                chat_id=chat_id,
                actor_id=actor_id,
                limit=limit,
                before_created_at=(
                    before_cursor.before_created_at if before_cursor is not None else None
                ),
                before_message_id=(
                    before_cursor.before_message_id if before_cursor is not None else None
                ),
            )
        )

        next_cursor: str | None = None
        if (
            response.has_more
            and response.next_before_created_at is not None
            and response.next_before_message_id is not None
        ):
            next_cursor = self._cursor_encrypter.encrypt(
                ChatHistoryCursor(
                    before_created_at=response.next_before_created_at,
                    before_message_id=response.next_before_message_id,
                )
            )

        return ChatHistoryEvent(
            messages=[ChatMessageEvent.from_entity(message) for message in response.messages],
            has_more=response.has_more,
            next_cursor=next_cursor,
        )
