from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from application.exceptions import (
    ActorNotFoundError,
    ChatMembershipForbiddenError,
    ChatNotFoundError,
)
from domain.entities.chat import ContextKind
from presentation.exceptions import ExpiredAccessTokenError, InvalidAccessTokenError
from presentation.handlers.chat_session import ChatSessionHandler
from presentation.ws.connection import StarletteChatConnectionAdapter

router = APIRouter()


@router.websocket("/ws/chats/{context_kind}/{context_external_id}")
@inject
async def chat_session(
    websocket: WebSocket,
    context_kind: ContextKind,
    context_external_id: str,
    token: Annotated[str, Query()],
    handler: FromDishka[ChatSessionHandler],
) -> None:
    try:
        await handler(
            token,
            context_kind,
            context_external_id,
            StarletteChatConnectionAdapter(websocket),
        )
    except InvalidAccessTokenError as error:
        await websocket.close(code=4401, reason=str(error))
    except ExpiredAccessTokenError as error:
        await websocket.close(code=4403, reason=str(error))
    except ChatNotFoundError as error:
        await websocket.close(code=4404, reason=str(error))
    except (ChatMembershipForbiddenError, ActorNotFoundError) as error:
        await websocket.close(code=4403, reason=str(error))
    except WebSocketDisconnect:
        return
