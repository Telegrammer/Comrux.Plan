from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, HTTPException, Query

from application.exceptions import (
    ActorNotFoundError,
    ChatMembershipForbiddenError,
    ChatNotFoundError,
)
from presentation.exceptions import (
    ExpiredAccessTokenError,
    InvalidAccessTokenError,
    InvalidCursorError,
)
from presentation.handlers import (
    ChatHistoryHandler,
    GetChatHistoryPageRequest,
    JoinChatMembershipHandler,
    JoinChatMembershipRequest,
    LeaveChatMembershipHandler,
    LeaveChatMembershipRequest,
)
from presentation.models import (
    ChatMembershipContextPayload,
    ChatHistoryEvent,
    ChatMemberJoinedEvent,
    ChatMemberLeavedEvent,
)

router = APIRouter()


@router.get("/chats/{chat_id}/messages")
@inject
async def get_chat_messages(
    chat_id: str,
    token: Annotated[str, Query()],
    handler: FromDishka[ChatHistoryHandler],
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1),
) -> ChatHistoryEvent:
    try:
        return await handler(
            GetChatHistoryPageRequest(
                token=token,
                chat_id=chat_id,
                limit=limit,
                cursor=cursor,
            )
        )
    except InvalidCursorError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except (InvalidAccessTokenError, ExpiredAccessTokenError) as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    except ChatNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except (ChatMembershipForbiddenError, ActorNotFoundError) as error:
        raise HTTPException(status_code=403, detail=str(error)) from error


@router.post("/chat-membership/self")
@inject
async def join_chat_membership(
    payload: ChatMembershipContextPayload,
    token: Annotated[str, Query()],
    handler: FromDishka[JoinChatMembershipHandler],
) -> ChatMemberJoinedEvent:
    try:
        return await handler(
            JoinChatMembershipRequest(
                token=token,
                context_kind=payload.context_kind,
                context_external_id=payload.context_external_id,
            )
        )
    except (InvalidAccessTokenError, ExpiredAccessTokenError) as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    except ChatNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except (ChatMembershipForbiddenError, ActorNotFoundError) as error:
        raise HTTPException(status_code=403, detail=str(error)) from error


@router.delete("/chat-membership/self")
@inject
async def leave_chat_membership(
    payload: ChatMembershipContextPayload,
    token: Annotated[str, Query()],
    handler: FromDishka[LeaveChatMembershipHandler],
) -> ChatMemberLeavedEvent:
    try:
        return await handler(
            LeaveChatMembershipRequest(
                token=token,
                context_kind=payload.context_kind,
                context_external_id=payload.context_external_id,
            )
        )
    except (InvalidAccessTokenError, ExpiredAccessTokenError) as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    except ChatNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except (ChatMembershipForbiddenError, ActorNotFoundError) as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
