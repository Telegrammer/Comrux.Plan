from dishka import Provider, Scope, from_context, provide
from redis.asyncio import Redis

from application.ports import (
    Clock,
    ChatRoomEventPublisher,
    ChatRoomFactory,
    ChatRoomRegistry,
    ChatRuntimeStore,
    ChatSessionSavePolicy,
)
from application.ports.gateways import DurableMessageCommandGateway
from application.services import (
    ChatRoomLifecycleHandler,
    ChatRoomPresenceHandler,
    ChatRoomSaver,
)
from setup.config import Settings

from infrastructure.chat_session import (
    InMemoryChatRoomRegistry,
    InMemoryChatRoomEventPublisher,
    LiveChatRoomFactory,
    RedisChatMessageMapper,
    RedisChatRuntimeStore,
)
from infrastructure.chat_session.save_policies import (
    CompositeChatSessionSavePolicy,
    DebounceChatSessionSavePolicy,
    PeriodicChatSessionSavePolicy,
)
from infrastructure.adapters.gateways import SQLAlchemyDurableMessageCommandGateway


class RuntimeProvider(Provider):
    scope = Scope.APP

    settings = from_context(Settings)

    @provide
    def redis_client(self, settings: Settings) -> Redis:
        return Redis.from_url(settings.redis.url, decode_responses=True)

    redis_message_mapper = provide(RedisChatMessageMapper)
    runtime_store = provide(
        source=RedisChatRuntimeStore,
        provides=ChatRuntimeStore,
    )
    room_registry = provide(
        source=InMemoryChatRoomRegistry,
        provides=ChatRoomRegistry,
    )
    durable_message_commands = provide(
        source=SQLAlchemyDurableMessageCommandGateway,
        provides=DurableMessageCommandGateway,
    )
    room_saver = provide(ChatRoomSaver)
    presence_handler = provide(ChatRoomPresenceHandler)

    @provide
    def save_policy(
        self,
        settings: Settings,
        room_saver: ChatRoomSaver,
        registry: ChatRoomRegistry,
    ) -> ChatSessionSavePolicy:
        return CompositeChatSessionSavePolicy(
            [
                DebounceChatSessionSavePolicy(
                    room_saver=room_saver,
                    delay=settings.chat_session.debounce_seconds,
                ),
                PeriodicChatSessionSavePolicy(
                    room_saver=room_saver,
                    registry=registry,
                    interval=settings.chat_session.periodic_seconds,
                    max_concurrent=settings.chat_session.periodic_max_concurrency,
                ),
            ]
        )

    @provide
    def lifecycle_handler(
        self,
        registry: ChatRoomRegistry,
        runtime_store: ChatRuntimeStore,
        room_saver: ChatRoomSaver,
        save_policy: ChatSessionSavePolicy,
    ) -> ChatRoomLifecycleHandler:
        return ChatRoomLifecycleHandler(
            registry=registry,
            runtime_store=runtime_store,
            saver=room_saver,
            save_policy=save_policy,
        )

    @provide
    def event_publisher(
        self,
        lifecycle_handler: ChatRoomLifecycleHandler,
        presence_handler: ChatRoomPresenceHandler,
    ) -> ChatRoomEventPublisher:
        publisher = InMemoryChatRoomEventPublisher()
        publisher.subscribe(lifecycle_handler)
        publisher.subscribe(presence_handler)
        return publisher

    @provide
    def room_factory(
        self,
        runtime_store: ChatRuntimeStore,
        clock: Clock,
        event_publisher: ChatRoomEventPublisher,
    ) -> ChatRoomFactory:
        return LiveChatRoomFactory(
            runtime_store=runtime_store,
            clock=clock,
            event_publisher=event_publisher,
        )
