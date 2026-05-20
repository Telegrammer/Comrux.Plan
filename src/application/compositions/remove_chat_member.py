import logging
from dataclasses import dataclass

from application.exceptions import ChatNotFoundError
from application.ports import ChatRoomRegistry, UnitOfWork
from application.ports.gateways import ChatQueryGateway
from application.services import ChatRoomSaver
from application.usecases import (
    CreateSystemMessageRequest,
    CreateSystemMessageUsecase,
    RemoveChatMemberRequest,
    RemoveChatMemberUsecase,
)
from domain.entities.actor import ActorId
from domain.entities.chat import ChatId, ContextRef

logger = logging.getLogger(__name__)


def _build_member_left_message(
    *, display_name: str, public_id: str, name: str
) -> str:
    return (
        "Member left: "
        f"name={name}, public_id={public_id}, display_name={display_name}"
    )


@dataclass(frozen=True)
class RemoveChatMemberCompositionRequest:
    context: ContextRef
    actor_id: ActorId


@dataclass(frozen=True)
class RemoveChatMemberCompositionResponse:
    chat_id: ChatId
    member_was_removed: bool
    display_name: str
    public_id: str
    name: str


class RemoveChatMemberComposition:
    def __init__(
        self,
        chat_queries: ChatQueryGateway,
        remove_chat_member: RemoveChatMemberUsecase,
        create_system_message: CreateSystemMessageUsecase,
        room_saver: ChatRoomSaver,
        room_registry: ChatRoomRegistry,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._chat_queries = chat_queries
        self._remove_chat_member = remove_chat_member
        self._create_system_message = create_system_message
        self._room_saver = room_saver
        self._room_registry = room_registry
        self._unit_of_work = unit_of_work

    async def __call__(
        self, request: RemoveChatMemberCompositionRequest
    ) -> RemoveChatMemberCompositionResponse:
        logger.info(
            "Chat membership remove started for %s:%s actor=%s",
            request.context.kind.value,
            request.context.external_id,
            request.actor_id.value,
        )

        async with self._unit_of_work:
            chat = await self._chat_queries.by_context(request.context)
            if chat is None:
                raise ChatNotFoundError(
                    "Chat for "
                    f"{request.context.kind.value}:{request.context.external_id} was not found"
                )

            member_response = await self._remove_chat_member(
                RemoveChatMemberRequest(chat_id=chat.id, actor_id=request.actor_id)
            )
            if member_response.was_removed:
                await self._create_system_message(
                    CreateSystemMessageRequest(
                        chat_id=chat.id,
                        content=_build_member_left_message(
                            display_name=member_response.display_name,
                            public_id=member_response.public_id,
                            name=member_response.name,
                        ),
                    )
                )

        if member_response.was_removed:
            await self._room_saver.save_if_dirty(member_response.chat_id)
            room = await self._room_registry.get(member_response.chat_id)
            if room is not None:
                await room.disconnect_actor(request.actor_id)

        logger.info(
            "Chat membership remove finished for chat=%s actor=%s removed=%s",
            member_response.chat_id.value,
            request.actor_id.value,
            member_response.was_removed,
        )
        return RemoveChatMemberCompositionResponse(
            chat_id=member_response.chat_id,
            member_was_removed=member_response.was_removed,
            display_name=member_response.display_name,
            public_id=member_response.public_id,
            name=member_response.name,
        )
