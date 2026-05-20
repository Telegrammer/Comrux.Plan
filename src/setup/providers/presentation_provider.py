from dishka import Provider, Scope, from_context, provide

from presentation.handlers import (
    ChatHistoryHandler,
    ChatSessionHandler,
    JoinChatMembershipHandler,
    LeaveChatMembershipHandler,
)
from presentation.presenters import CursorEncrypter, FernetCursorEncrypter
from presentation.presenters.auth import JwtAccessTokenPresenter
from setup.config import Settings


class PresentationProvider(Provider):
    scope = Scope.SESSION

    settings = from_context(Settings, scope=Scope.APP)

    @provide
    def token_presenter(self, settings: Settings) -> JwtAccessTokenPresenter:
        return JwtAccessTokenPresenter(
            public_key=settings.auth.public_key_path.read_text(),
            algorithm=settings.auth.algorithm,
        )

    @provide
    def cursor_encrypter(self, settings: Settings) -> CursorEncrypter:
        return FernetCursorEncrypter(settings.service.encryption_key)

    chat_session_handler = provide(ChatSessionHandler)
    chat_history_handler = provide(ChatHistoryHandler)
    # These HTTP handlers depend on application-layer request-scoped compositions/usecases.
    # Keep them request-scoped to satisfy Dishka scope validation.
    join_chat_membership_handler = provide(JoinChatMembershipHandler, scope=Scope.REQUEST)
    leave_chat_membership_handler = provide(LeaveChatMembershipHandler, scope=Scope.REQUEST)
