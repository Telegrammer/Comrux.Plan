import logging
from dataclasses import dataclass

from application.ports import UnitOfWork
from application.usecases import (
    AddChatMemberRequest,
    AddChatMemberUsecase,
    CreateChatRequest,
    CreateChatUsecase,
    CreateSystemMessageRequest,
    CreateSystemMessageUsecase,
)
from domain.entities.actor import ActorId
from domain.entities.chat import ChatId

logger = logging.getLogger(__name__)

SYSTEM_CHAT_CREATED_MESSAGE = "Chat created"


@dataclass(frozen=True)
class CreateProjectChatRequest:
    chat: CreateChatRequest
    owner_id: ActorId


@dataclass(frozen=True)
class CreateProjectChatResponse:
    chat_id: ChatId
    chat_was_created: bool
    owner_was_added: bool


class CreateProjectChatComposition:
    def __init__(
        self,
        create_chat: CreateChatUsecase,
        add_chat_member: AddChatMemberUsecase,
        create_system_message: CreateSystemMessageUsecase,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._create_chat = create_chat
        self._add_chat_member = add_chat_member
        self._create_system_message = create_system_message
        self._unit_of_work = unit_of_work

    async def __call__(
        self, request: CreateProjectChatRequest
    ) -> CreateProjectChatResponse:
        logger.info(
            "Project chat creation started for %s:%s",
            request.chat.context.kind.value,
            request.chat.context.external_id,
        )

        async with self._unit_of_work:
            chat_response = await self._create_chat(request.chat)
            owner_response = await self._add_chat_member(
                AddChatMemberRequest(
                    chat_id=chat_response.chat_id,
                    actor_id=request.owner_id,
                )
            )
            if chat_response.was_created:
                await self._create_system_message(
                    CreateSystemMessageRequest(
                        chat_id=chat_response.chat_id,
                        content=SYSTEM_CHAT_CREATED_MESSAGE,
                    )
                )

        logger.info(
            "Project chat %s ready (created=%s, owner_added=%s)",
            chat_response.chat_id.value,
            chat_response.was_created,
            owner_response.was_added,
        )
        return CreateProjectChatResponse(
            chat_id=chat_response.chat_id,
            chat_was_created=chat_response.was_created,
            owner_was_added=owner_response.was_added,
        )
