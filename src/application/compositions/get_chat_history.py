import logging
from dataclasses import dataclass
from datetime import datetime

from application.ports import ChatMessage, UnitOfWork
from application.usecases import (
    GetChatHistoryRequest,
    GetChatHistoryUsecase,
    RequireChatAccessRequest,
    RequireChatAccessUsecase,
)
from domain.entities.actor import ActorId
from domain.entities.chat import ChatId

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GetChatHistoryCompositionRequest:
    chat_id: ChatId
    actor_id: ActorId
    limit: int
    before_created_at: datetime | None = None
    before_message_id: int | None = None


@dataclass(frozen=True)
class GetChatHistoryCompositionResponse:
    messages: list[ChatMessage]
    has_more: bool
    next_before_created_at: datetime | None
    next_before_message_id: int | None


class GetChatHistoryComposition:
    def __init__(
        self,
        require_access: RequireChatAccessUsecase,
        get_history: GetChatHistoryUsecase,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._require_access = require_access
        self._get_history = get_history
        self._unit_of_work = unit_of_work

    async def __call__(
        self, request: GetChatHistoryCompositionRequest
    ) -> GetChatHistoryCompositionResponse:
        logger.info(
            "Chat history loading started for chat=%s actor=%s limit=%s",
            request.chat_id.value,
            request.actor_id.value,
            request.limit,
        )
        async with self._unit_of_work:
            await self._require_access(
                RequireChatAccessRequest(
                    chat_id=request.chat_id,
                    actor_id=request.actor_id,
                )
            )
            response = await self._get_history(
                GetChatHistoryRequest(
                    chat_id=request.chat_id,
                    limit=request.limit,
                    before_created_at=request.before_created_at,
                    before_message_id=request.before_message_id,
                )
            )

        logger.info(
            "Chat history loaded for chat=%s actor=%s messages=%s has_more=%s",
            request.chat_id.value,
            request.actor_id.value,
            len(response.messages),
            response.has_more,
        )
        return GetChatHistoryCompositionResponse(
            messages=response.messages,
            has_more=response.has_more,
            next_before_created_at=response.next_before_created_at,
            next_before_message_id=response.next_before_message_id,
        )
