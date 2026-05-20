from dishka import Provider, Scope, provide

from application.compositions import (
    AddProjectMemberComposition,
    CreateActorComposition,
    CreateChatComposition,
    CreateProjectChatComposition,
    FlushChatRoomMessagesComposition,
    GetChatHistoryComposition,
    JoinChatMembershipComposition,
    RemoveChatMemberComposition,
)
from application.ports import Clock
from application.ports.gateways import (
    ActorCommandGateway,
    ActorQueryGateway,
    ChatCommandGateway,
    ChatMembershipCommandGateway,
    ChatMembershipQueryGateway,
    ChatQueryGateway,
    MessageCommandGateway,
    MessageQueryGateway,
)
from application.usecases import (
    AddChatMemberUsecase,
    CreateActorUsecase,
    CreateChatUsecase,
    RemoveChatMemberUsecase,
    CreateUserMessageUsecase,
    CreateSystemMessageUsecase,
    GetChatHistoryUsecase,
    JoinChatRoomUsecase,
    RequireChatAccessUsecase,
    ServeChatConnectionUsecase,
)
from infrastructure.adapters import TimestampClock
from infrastructure.adapters.gateways import (
    SQLAlchemyActorCommandGateway,
    SQLAlchemyActorQueryGateway,
    SQLAlchemyChatCommandGateway,
    SQLAlchemyChatMembershipCommandGateway,
    SQLAlchemyChatMembershipQueryGateway,
    SQLAlchemyChatQueryGateway,
    SQLAlchemyMessageCommandGateway,
)
from infrastructure.adapters.mappers import SQLAlchemyChatMapper


class ApplicationProvider(Provider):
    scope = Scope.REQUEST

    clock = provide(source=TimestampClock, provides=Clock, scope=Scope.APP)

    chat_mapper = provide(SQLAlchemyChatMapper, scope=Scope.SESSION)

    actor_command_gateway = provide(
        source=SQLAlchemyActorCommandGateway,
        provides=ActorCommandGateway,
        scope=Scope.SESSION,
    )
    actor_query_gateway = provide(
        source=SQLAlchemyActorQueryGateway,
        provides=ActorQueryGateway,
        scope=Scope.SESSION,
    )
    chat_command_gateway = provide(
        source=SQLAlchemyChatCommandGateway,
        provides=ChatCommandGateway,
        scope=Scope.SESSION,
    )
    chat_membership_command_gateway = provide(
        source=SQLAlchemyChatMembershipCommandGateway,
        provides=ChatMembershipCommandGateway,
        scope=Scope.SESSION,
    )
    chat_membership_query_gateway = provide(
        source=SQLAlchemyChatMembershipQueryGateway,
        provides=ChatMembershipQueryGateway,
        scope=Scope.SESSION,
    )
    chat_query_gateway = provide(
        source=SQLAlchemyChatQueryGateway,
        provides=ChatQueryGateway,
        scope=Scope.SESSION,
    )
    message_command_gateway = provide(
        source=SQLAlchemyMessageCommandGateway,
        provides=MessageCommandGateway,
        scope=Scope.SESSION,
    )
    message_query_gateway = provide(
        source=SQLAlchemyMessageCommandGateway,
        provides=MessageQueryGateway,
        scope=Scope.SESSION,
    )

    create_actor_usecase = provide(CreateActorUsecase)
    create_chat_usecase = provide(CreateChatUsecase)
    add_chat_member_usecase = provide(AddChatMemberUsecase)
    remove_chat_member_usecase = provide(RemoveChatMemberUsecase)
    create_system_message_usecase = provide(CreateSystemMessageUsecase)
    create_user_message_usecase = provide(CreateUserMessageUsecase, scope=Scope.SESSION)
    get_chat_history_usecase = provide(GetChatHistoryUsecase, scope=Scope.SESSION)
    require_chat_access_usecase = provide(RequireChatAccessUsecase, scope=Scope.SESSION)
    join_chat_room_usecase = provide(JoinChatRoomUsecase, scope=Scope.SESSION)
    serve_chat_connection_usecase = provide(
        ServeChatConnectionUsecase, scope=Scope.SESSION
    )

    create_actor_composition = provide(CreateActorComposition)
    create_chat_composition = provide(CreateChatComposition)
    create_project_chat_composition = provide(CreateProjectChatComposition)
    add_project_member_composition = provide(AddProjectMemberComposition)
    join_chat_membership_composition = provide(JoinChatMembershipComposition)
    remove_chat_member_composition = provide(RemoveChatMemberComposition)
    flush_chat_room_messages_composition = provide(
        FlushChatRoomMessagesComposition, scope=Scope.SESSION
    )
    get_chat_history_composition = provide(GetChatHistoryComposition, scope=Scope.SESSION)