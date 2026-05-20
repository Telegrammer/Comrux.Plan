from dataclasses import dataclass
from datetime import datetime

from application.ports import ChatMessage, ChatRuntimeStore
from application.ports.gateways import MessageQueryGateway
from domain.entities.chat import ChatId


@dataclass(frozen=True)
class GetChatHistoryRequest:
    chat_id: ChatId
    limit: int
    before_created_at: datetime | None = None
    before_message_id: int | None = None


@dataclass(frozen=True)
class GetChatHistoryResponse:
    messages: list[ChatMessage]
    has_more: bool
    next_before_created_at: datetime | None
    next_before_message_id: int | None


class GetChatHistoryUsecase:
    def __init__(
        self,
        message_queries: MessageQueryGateway,
        runtime_store: ChatRuntimeStore,
    ) -> None:
        self._message_queries = message_queries
        self._runtime_store = runtime_store

    async def __call__(
        self, request: GetChatHistoryRequest
    ) -> GetChatHistoryResponse:
        limit = max(request.limit, 1)
        persisted_messages = await self._message_queries.recent_by_chat(
            request.chat_id,
            limit + 1,
            before_created_at=request.before_created_at,
            before_message_id=request.before_message_id,
        )

        has_more = len(persisted_messages) > limit
        if has_more:
            persisted_messages = persisted_messages[1:]

        history = list(persisted_messages)
        if request.before_created_at is None:
            pending_messages = await self._runtime_store.list_pending_messages(request.chat_id)
            history.extend(pending_messages)

        history.sort(
            key=lambda message: (
                message.created_at,
                message.message_id.value if message.message_id is not None else 0,
                message.runtime_id or "",
            )
        )
        page = history[-limit:]

        next_before_created_at: datetime | None = None
        next_before_message_id: int | None = None
        if has_more:
            first_persisted = next(
                (message for message in page if message.message_id is not None),
                None,
            )
            if first_persisted is not None and first_persisted.message_id is not None:
                next_before_created_at = first_persisted.created_at
                next_before_message_id = first_persisted.message_id.value
            else:
                has_more = False

        return GetChatHistoryResponse(
            messages=page,
            has_more=has_more,
            next_before_created_at=next_before_created_at,
            next_before_message_id=next_before_message_id,
        )
