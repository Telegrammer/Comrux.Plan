from collections.abc import Awaitable, Callable
import asyncio
from uuid import uuid4

from application.exceptions import ConnectionClosedError
from application.ports import (
    ChatErrorEvent,
    ChatConnection,
    ChatMemberJoinedEvent,
    ChatMemberLeftEvent,
    ChatMessage,
    ChatMessageCreatedEvent,
    ChatRoomEventPublisher,
    ChatRoom,
    ChatRuntimeStore,
    Clock,
    PingCommand,
    PongEvent,
    SendChatMessageCommand,
)
from domain.entities.actor import Actor, ActorId
from domain.entities.chat import ChatId
from domain.entities.message import MessageAuthorKind, MessageId


class LiveChatRoom(ChatRoom):
    def __init__(
        self,
        chat_id: ChatId,
        runtime_store: ChatRuntimeStore,
        clock: Clock,
        event_publisher: ChatRoomEventPublisher,
    ) -> None:
        self._chat_id = chat_id
        self._runtime_store = runtime_store
        self._clock = clock
        self._events = event_publisher
        self._dirty = False
        self._lock = asyncio.Lock()
        self._connections: dict[int, ChatConnection] = {}
        self._connection_owners: dict[int, ActorId] = {}

    @property
    def chat_id(self) -> ChatId:
        return self._chat_id

    @property
    def is_dirty(self) -> bool:
        return self._dirty

    @property
    def is_empty(self) -> bool:
        return not self._connections

    async def pending_messages(self) -> list[ChatMessage]:
        return await self._runtime_store.list_pending_messages(self._chat_id)

    async def mark_persisted(self, runtime_ids: list[str]) -> None:
        await self._runtime_store.delete_pending_messages(self._chat_id, runtime_ids)

    def mark_clean(self) -> None:
        self._dirty = False

    async def serve(self, actor: Actor, connection: ChatConnection) -> None:
        await self._join(actor, connection)
        try:
            while True:
                command = await connection.receive()
                await self._handle_command(actor, connection, command)
        except ConnectionClosedError:
            return
        finally:
            await self._leave(actor, connection)

    async def disconnect_actor(self, actor_id: ActorId) -> int:
        async with self._lock:
            actor_connections = [
                connection
                for connection_id, connection in self._connections.items()
                if self._connection_owners.get(connection_id) == actor_id
            ]

        disconnected_count = 0
        for connection in actor_connections:
            try:
                await connection.close()
            except ConnectionClosedError:
                continue
            disconnected_count += 1
        return disconnected_count

    async def _join(self, actor: Actor, connection: ChatConnection) -> None:
        async with self._lock:
            connection_id = id(connection)
            self._connections[connection_id] = connection
            self._connection_owners[connection_id] = actor.id
            peers = list(self._connections.values())

        await self._broadcast(
            ChatMemberJoinedEvent(
                chat_id=self._chat_id,
                actor_id=actor.id,
                display_name=actor.display_name.value,
            ),
            peers,
        )

    async def _leave(self, actor: Actor, connection: ChatConnection) -> None:
        async with self._lock:
            connection_id = id(connection)
            self._connections.pop(connection_id, None)
            self._connection_owners.pop(connection_id, None)
            peers = list(self._connections.values())

        await self._broadcast(
            ChatMemberLeftEvent(
                chat_id=self._chat_id,
                actor_id=actor.id,
                display_name=actor.display_name.value,
            ),
            peers,
        )

    async def _handle_command(
        self,
        actor: Actor,
        connection: ChatConnection,
        command: PingCommand | SendChatMessageCommand,
    ) -> None:
        if isinstance(command, PingCommand):
            await connection.send(PongEvent())
            return
        if not isinstance(command, SendChatMessageCommand):
            await connection.send(
                ChatErrorEvent(
                    code="invalid_event",
                    message="Unsupported event type",
                )
            )
            return

        if not command.content.strip():
            await connection.send(
                ChatErrorEvent(
                    code="invalid_message",
                    message="Message content cannot be empty",
                )
            )
            return

        runtime_message = ChatMessage(
            chat_id=self._chat_id,
            content=command.content.strip(),
            created_at=self._clock.now(),
            author_kind=MessageAuthorKind.USER,
            runtime_id=str(uuid4()),
            author_id=actor.id,
            author_display_name=actor.display_name.value,
            reply_to_message_id=command.reply_to_message_id,
            persisted=False,
        )
        await self._runtime_store.append_pending_message(runtime_message)
        self._dirty = True
        await self._broadcast(
            ChatMessageCreatedEvent(message=runtime_message),
            list(self._connections.values()),
        )
        await self._events.publish_room_modified(self._chat_id)

    async def _broadcast(
        self,
        event: ChatMemberJoinedEvent | ChatMemberLeftEvent | ChatMessageCreatedEvent,
        connections: list[ChatConnection],
    ) -> None:
        for peer in connections:
            try:
                await peer.send(event)
            except ConnectionClosedError:
                continue
