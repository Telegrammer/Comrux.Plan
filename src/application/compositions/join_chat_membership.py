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
from domain.entities.chat import ChatId, ContextRef

logger = logging.getLogger(__name__)

SYSTEM_CHAT_CREATED_MESSAGE = "Chat created"


def _build_member_added_message(*, display_name: str, public_id: str) -> str:
    return f"Member added: public_id={public_id}, display_name={display_name}"


@dataclass(frozen=True)
class JoinChatMembershipCompositionRequest:
    context: ContextRef
    actor_id: ActorId


@dataclass(frozen=True)
class JoinChatMembershipCompositionResponse:
    chat_id: ChatId
    chat_was_created: bool
    member_was_added: bool


class JoinChatMembershipComposition:
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
        self, request: JoinChatMembershipCompositionRequest
    ) -> JoinChatMembershipCompositionResponse:
        logger.info(
            "Chat membership join started for %s:%s actor=%s",
            request.context.kind.value,
            request.context.external_id,
            request.actor_id.value,
        )
        async with self._unit_of_work:
            chat_response = await self._create_chat(
                CreateChatRequest(name=None, context=request.context)
            )
            member_response = await self._add_chat_member(
                AddChatMemberRequest(
                    chat_id=chat_response.chat_id,
                    actor_id=request.actor_id,
                )
            )
            if chat_response.was_created:
                await self._create_system_message(
                    CreateSystemMessageRequest(
                        chat_id=chat_response.chat_id,
                        content=SYSTEM_CHAT_CREATED_MESSAGE,
                    )
                )
            if member_response.was_added:
                await self._create_system_message(
                    CreateSystemMessageRequest(
                        chat_id=chat_response.chat_id,
                        content=_build_member_added_message(
                            display_name=member_response.display_name,
                            public_id=member_response.public_id,
                        ),
                    )
                )

        logger.info(
            "Chat membership join finished for chat=%s actor=%s (chat_created=%s, member_added=%s)",
            chat_response.chat_id.value,
            request.actor_id.value,
            chat_response.was_created,
            member_response.was_added,
        )
        return JoinChatMembershipCompositionResponse(
            chat_id=chat_response.chat_id,
            chat_was_created=chat_response.was_created,
            member_was_added=member_response.was_added,
        )
