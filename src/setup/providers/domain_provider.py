from dishka import Provider, Scope, from_context, provide

from domain.ports import MessageContentEncrypter
from domain.services import ActorService, ChatService, MessageService
from domain.value_objects import MessageEncryptionKey
from infrastructure.adapters import (
    FernetMessageContentEncrypter,
    Uuid7ChatIdGenerator,
)
from setup.config import Settings


class DomainProvider(Provider):
    scope = Scope.APP

    settings = from_context(Settings)

    @provide
    def provide_encryption_key(self, settings: Settings) -> MessageEncryptionKey:
        return MessageEncryptionKey(settings.service.encryption_key)

    message_content_encrypter = provide(
        source=FernetMessageContentEncrypter,
        provides=MessageContentEncrypter,
    )

    @provide
    def provide_chat_service(self) -> ChatService:
        return ChatService(id_generator=Uuid7ChatIdGenerator())

    actor_service = provide(ActorService)
    message_service = provide(MessageService)
