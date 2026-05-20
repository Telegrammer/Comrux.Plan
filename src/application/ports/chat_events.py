from abc import ABC, abstractmethod
from dataclasses import dataclass

from domain.entities.actor import Actor
from domain.entities.chat import ChatId


@dataclass(frozen=True)
class ChatRoomEvent(ABC):
    chat_id: ChatId

    @abstractmethod
    async def accept(self, listener: "ChatRoomEventListener") -> None:
        raise NotImplementedError


@dataclass(frozen=True)
class ChatActorEvent(ChatRoomEvent, ABC):
    actor: Actor


@dataclass(frozen=True)
class ChatClientJoinedEvent(ChatActorEvent):
    async def accept(self, listener: "ChatRoomEventListener") -> None:
        await listener.on_client_joined(self)


@dataclass(frozen=True)
class ChatClientLeftEvent(ChatActorEvent):
    async def accept(self, listener: "ChatRoomEventListener") -> None:
        await listener.on_client_left(self)


@dataclass(frozen=True)
class ChatRoomModifiedEvent(ChatRoomEvent):
    async def accept(self, listener: "ChatRoomEventListener") -> None:
        await listener.on_room_modified(self)


class ChatRoomEventListener(ABC):
    @abstractmethod
    async def on_client_joined(self, event: ChatClientJoinedEvent) -> None:
        raise NotImplementedError

    @abstractmethod
    async def on_client_left(self, event: ChatClientLeftEvent) -> None:
        raise NotImplementedError

    @abstractmethod
    async def on_room_modified(self, event: ChatRoomModifiedEvent) -> None:
        raise NotImplementedError


class ChatRoomEventPublisher(ABC):
    @abstractmethod
    def subscribe(self, listener: ChatRoomEventListener) -> None:
        raise NotImplementedError

    @abstractmethod
    async def publish_client_joined(self, chat_id: ChatId, actor: Actor) -> None:
        raise NotImplementedError

    @abstractmethod
    async def publish_client_left(self, chat_id: ChatId, actor: Actor) -> None:
        raise NotImplementedError

    @abstractmethod
    async def publish_room_modified(self, chat_id: ChatId) -> None:
        raise NotImplementedError
