from dishka import Provider, Scope, provide

from application.compositions import (
    AddProjectMemberComposition,
    CreateActorComposition,
    CreateChatComposition,
    CreateProjectChatComposition,
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
)
from application.usecases import (
    AddChatMemberUsecase,
    CreateActorUsecase,
    CreateChatUsecase,
    CreateSystemMessageUsecase,
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

    chat_mapper = provide(SQLAlchemyChatMapper, scope=Scope.REQUEST)

    actor_command_gateway = provide(
        source=SQLAlchemyActorCommandGateway,
        provides=ActorCommandGateway,
    )
    actor_query_gateway = provide(
        source=SQLAlchemyActorQueryGateway,
        provides=ActorQueryGateway,
    )
    chat_command_gateway = provide(
        source=SQLAlchemyChatCommandGateway,
        provides=ChatCommandGateway,
    )
    chat_membership_command_gateway = provide(
        source=SQLAlchemyChatMembershipCommandGateway,
        provides=ChatMembershipCommandGateway,
    )
    chat_membership_query_gateway = provide(
        source=SQLAlchemyChatMembershipQueryGateway,
        provides=ChatMembershipQueryGateway,
    )
    chat_query_gateway = provide(
        source=SQLAlchemyChatQueryGateway,
        provides=ChatQueryGateway,
    )
    message_command_gateway = provide(
        source=SQLAlchemyMessageCommandGateway,
        provides=MessageCommandGateway,
    )

    create_actor_usecase = provide(CreateActorUsecase)
    create_chat_usecase = provide(CreateChatUsecase)
    add_chat_member_usecase = provide(AddChatMemberUsecase)
    create_system_message_usecase = provide(CreateSystemMessageUsecase)

    create_actor_composition = provide(CreateActorComposition)
    create_chat_composition = provide(CreateChatComposition)
    create_project_chat_composition = provide(CreateProjectChatComposition)
    add_project_member_composition = provide(AddProjectMemberComposition)
