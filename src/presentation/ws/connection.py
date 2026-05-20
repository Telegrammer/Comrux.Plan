from starlette.websockets import WebSocket, WebSocketDisconnect

from application.exceptions import ConnectionClosedError
from application.ports import (
    ChatErrorEvent,
    ChatHistoryEvent,
    ChatMemberJoinedEvent,
    ChatMemberLeftEvent,
    ChatMessage,
    ChatMessageCreatedEvent,
    ChatSessionCommand,
    ChatSessionEvent,
    PingCommand,
    PongEvent,
    SendChatMessageCommand,
)
from domain.entities.message import MessageId


class StarletteChatConnectionAdapter:
    def __init__(self, websocket: WebSocket) -> None:
        self._websocket = websocket

    async def accept(self) -> None:
        await self._websocket.accept()

    async def receive(self) -> ChatSessionCommand:
        try:
            payload = await self._websocket.receive_json()
        except WebSocketDisconnect as error:
            raise ConnectionClosedError from error
        if not isinstance(payload, dict):
            return PingCommand()

        event_type = payload.get("type")
        if event_type == "send_message":
            return SendChatMessageCommand(
                content=str(payload.get("content", "")),
                reply_to_message_id=(
                    MessageId(payload["reply_to_message_id"])
                    if isinstance(payload.get("reply_to_message_id"), int)
                    else None
                ),
            )
        return PingCommand()

    async def send(self, event: ChatSessionEvent) -> None:
        try:
            await self._websocket.send_json(self._serialize_event(event))
        except WebSocketDisconnect as error:
            raise ConnectionClosedError from error

    async def close(self) -> None:
        await self._websocket.close()

    def _serialize_event(self, event: ChatSessionEvent) -> dict[str, object]:
        if isinstance(event, PongEvent):
            return {"type": "pong"}
        if isinstance(event, ChatErrorEvent):
            return {"type": "error", "code": event.code, "message": event.message}
        if isinstance(event, ChatHistoryEvent):
            return {
                "type": "history",
                "chat_id": str(event.chat_id.value),
                "messages": [
                    self._serialize_message(message) for message in event.messages
                ],
            }
        if isinstance(event, ChatMessageCreatedEvent):
            return {
                "type": "message_created",
                **self._serialize_message(event.message),
            }
        if isinstance(event, ChatMemberJoinedEvent):
            return {
                "type": "member_joined",
                "chat_id": str(event.chat_id.value),
                "actor_id": str(event.actor_id.value),
                "display_name": event.display_name,
            }
        if isinstance(event, ChatMemberLeftEvent):
            return {
                "type": "member_left",
                "chat_id": str(event.chat_id.value),
                "actor_id": str(event.actor_id.value),
                "display_name": event.display_name,
            }
        raise TypeError(f"Unsupported event type: {type(event).__name__}")

    def _serialize_message(self, message: ChatMessage) -> dict[str, object]:
        return {
            "chat_id": str(message.chat_id.value),
            "message_id": message.message_id.value if message.message_id else None,
            "runtime_id": message.runtime_id,
            "author_id": str(message.author_id.value) if message.author_id else None,
            "author_display_name": message.author_display_name,
            "author_kind": message.author_kind.value,
            "content": message.content,
            "created_at": message.created_at.isoformat(),
            "reply_to_message_id": (
                message.reply_to_message_id.value
                if message.reply_to_message_id is not None
                else None
            ),
            "persisted": message.persisted,
        }
