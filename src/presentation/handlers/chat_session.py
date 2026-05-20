from application.ports import ChatConnection, ChatHistoryEvent
from application.usecases import (
    JoinChatRoomRequest,
    JoinChatRoomUsecase,
    ServeChatConnectionRequest,
    ServeChatConnectionUsecase,
)
from domain.entities.actor import ActorId
from domain.entities.chat import ContextKind, ContextRef
from setup.config import Settings

from uuid import UUID
from presentation.exceptions import InvalidAccessTokenError
from presentation.presenters.auth import JwtAccessTokenPresenter


class ChatSessionHandler:
    def __init__(
        self,
        settings: Settings,
        token_presenter: JwtAccessTokenPresenter,
        join_usecase: JoinChatRoomUsecase,
        serve_usecase: ServeChatConnectionUsecase,
    ) -> None:
        self._settings = settings
        self._token_presenter = token_presenter
        self._join_usecase = join_usecase
        self._serve_usecase = serve_usecase

    async def __call__(
        self,
        token: str,
        context_kind: ContextKind,
        context_external_id: str,
        connection: ChatConnection,
    ) -> None:
        auth_info = self._token_presenter.present(token)
        try:
            actor_id = ActorId(UUID(auth_info.user_id))
        except ValueError as error:
            raise InvalidAccessTokenError("Token contains invalid user_id") from error

        joined = await self._join_usecase(
            JoinChatRoomRequest(
                context=ContextRef(
                    kind=context_kind,
                    external_id=context_external_id,
                ),
                actor_id=actor_id,
                history_limit=self._settings.chat_session.history_limit,
            )
        )

        await connection.accept()
        await connection.send(
            ChatHistoryEvent(chat_id=joined.room.chat_id, messages=joined.history)
        )
        await self._serve_usecase(
            ServeChatConnectionRequest(
                room=joined.room,
                actor=joined.actor,
                connection=connection,
            )
        )
