import logging
from uuid import UUID

from dishka.integrations.faststream import FromDishka, inject
from faststream.kafka import KafkaRouter

from application.compositions import (
    AddProjectMemberComposition,
    CreateActorComposition,
    CreateProjectChatComposition,
    RemoveChatMemberComposition,
    RemoveChatMemberCompositionRequest,
)
from application.ports import UnitOfWork
from application.usecases import (
    CreateActorRequest,
    CreateChatRequest,
    CreateChatUsecase,
    CreateSystemMessageRequest,
    CreateSystemMessageUsecase,
)
from application.compositions.add_project_member import AddProjectMemberRequest
from application.compositions.create_project_chat import CreateProjectChatRequest
from domain.entities.actor import ActorId
from domain.entities.chat import ContextKind
from domain.exceptions import DomainFieldError

from .models import (
    ProjectCreated,
    ProjectTaskCreated,
    ProjectTaskStatusChanged,
    ProjectMemberAdded,
    ProjectMemberRemoved,
    UserCreated,
)

logger = logging.getLogger(__name__)

chat_sub_router = KafkaRouter()


@chat_sub_router.subscriber(
    "user.created", group_id="chat-service", auto_offset_reset="earliest"
)
@inject
async def create_actor(
    usecase: FromDishka[CreateActorComposition], message: UserCreated
) -> None:
    try:
        response = await usecase(
            CreateActorRequest.from_primitives(
                actor_id=message.user_id,
                display_name=message.name,
                email=message.email,
            )
        )
    except KeyError:
        raise DomainFieldError("Received wrong data")

    if response.was_created:
        logger.info("Created actor %s", message.user_id)
    else:
        logger.info("Actor %s already exists", message.user_id)


@chat_sub_router.subscriber(
    "project.created", group_id="chat-service", auto_offset_reset="earliest"
)
@inject
async def create_project_chat(
    usecase: FromDishka[CreateProjectChatComposition], message: ProjectCreated
) -> None:
    try:
        response = await usecase(
            CreateProjectChatRequest(
                chat=CreateChatRequest.from_primitives(
                    name=None,
                    context_kind=ContextKind.PROJECT,
                    ref=message.project_id,
                ),
                owner_id=ActorId(UUID(message.owner_id)),
            )
        )
    except KeyError:
        raise DomainFieldError("Received wrong data")

    if response.chat_was_created:
        logger.info("Created chat for project %s", message.project_id)
    else:
        logger.info("Chat for project %s already exists", message.project_id)


@chat_sub_router.subscriber(
    "project.member_added", group_id="chat-service", auto_offset_reset="earliest"
)
@inject
async def add_project_member(
    usecase: FromDishka[AddProjectMemberComposition], message: ProjectMemberAdded
) -> None:
    try:
        response = await usecase(
            AddProjectMemberRequest(
                chat=CreateChatRequest.from_primitives(
                    name=None,
                    context_kind=ContextKind.PROJECT,
                    ref=message.project_id,
                ),
                actor_id=ActorId(UUID(message.member_id)),
            )
        )
    except KeyError:
        raise DomainFieldError("Received wrong data")

    if response.member_was_added:
        logger.info(
            "Added actor %s to project chat %s", message.member_id, message.project_id
        )
    else:
        logger.info(
            "Actor %s already belongs to project chat %s",
            message.member_id,
            message.project_id,
        )


@chat_sub_router.subscriber(
    "project.member_removed", group_id="chat-service", auto_offset_reset="earliest"
)
@inject
async def remove_project_member(
    usecase: FromDishka[RemoveChatMemberComposition], message: ProjectMemberRemoved
) -> None:
    try:
        response = await usecase(
            RemoveChatMemberCompositionRequest(
                context=CreateChatRequest.from_primitives(
                    name=None,
                    context_kind=ContextKind.PROJECT,
                    ref=message.project_id,
                ).context,
                actor_id=ActorId(UUID(message.member_id)),
            )
        )
    except KeyError:
        raise DomainFieldError("Received wrong data")

    if response.member_was_removed:
        logger.info(
            "Removed actor %s from project chat %s", message.member_id, message.project_id
        )
    else:
        logger.info(
            "Actor %s was already absent in project chat %s",
            message.member_id,
            message.project_id,
        )


@chat_sub_router.subscriber(
    "project.task.created", group_id="chat-service", auto_offset_reset="earliest"
)
@inject
async def notify_project_task_created(
    create_chat_usecase: FromDishka[CreateChatUsecase],
    create_system_message_usecase: FromDishka[CreateSystemMessageUsecase],
    unit_of_work: FromDishka[UnitOfWork],
    message: ProjectTaskCreated,
) -> None:
    short_task_id = message.task_id[:6]
    task_label = (
        f'"{message.title}" ({short_task_id})' if message.title else short_task_id
    )
    async with unit_of_work:
        chat = await create_chat_usecase(
            CreateChatRequest.from_primitives(
                name=None,
                context_kind=ContextKind.PROJECT,
                ref=message.project_id,
            )
        )
        await create_system_message_usecase(
            CreateSystemMessageRequest(
                chat_id=chat.chat_id,
                content=f"Task created: {task_label}",
            )
            )
    logger.info("Published task-created message in project chat %s", message.project_id)


@chat_sub_router.subscriber(
    "project.task.status_changed", group_id="chat-service", auto_offset_reset="earliest"
)
@inject
async def notify_project_task_status_changed(
    create_chat_usecase: FromDishka[CreateChatUsecase],
    create_system_message_usecase: FromDishka[CreateSystemMessageUsecase],
    unit_of_work: FromDishka[UnitOfWork],
    message: ProjectTaskStatusChanged,
) -> None:
    short_task_id = message.task_id[:6]
    task_label = (
        f'"{message.title}" ({short_task_id})' if message.title else short_task_id
    )
    async with unit_of_work:
        chat = await create_chat_usecase(
            CreateChatRequest.from_primitives(
                name=None,
                context_kind=ContextKind.PROJECT,
                ref=message.project_id,
            )
        )
        await create_system_message_usecase(
            CreateSystemMessageRequest(
                chat_id=chat.chat_id,
                content=f"Task {task_label} moved to {message.status}",
            )
        )
    logger.info(
        "Published task-status message in project chat %s",
        message.project_id,
    )
