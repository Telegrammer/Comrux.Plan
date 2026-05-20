from datetime import UTC, datetime
from uuid import UUID

import pytest

from application.compositions import (
    FlushChatRoomMessagesComposition,
    FlushChatRoomMessagesRequest,
)
from application.ports import ChatMessage, Transaction, UnitOfWork
from application.ports.gateways import MessageCommandGateway
from domain.entities.actor import ActorId
from domain.entities.chat import ChatId
from domain.entities.message import Message, MessageAuthorKind
from domain.services import MessageService


class InMemoryMessageCommandGateway(MessageCommandGateway):
    def __init__(self) -> None:
        self.saved_messages: list[Message] = []

    async def add(self, message: Message) -> None:
        self.saved_messages.append(message)

    async def add_many(self, messages: list[Message]) -> None:
        self.saved_messages.extend(messages)


class StubTransaction(Transaction):
    def __init__(self) -> None:
        self.completed = False
        self.cancelled = False

    async def complete(self) -> None:
        self.completed = True

    async def cancel(self) -> None:
        self.cancelled = True


class StubUnitOfWork(UnitOfWork):
    def __init__(self) -> None:
        self._transactions: list[Transaction] = [StubTransaction()]

    def add(self, transaction: Transaction) -> None:
        self._transactions.append(transaction)

    async def __aenter__(self) -> "StubUnitOfWork":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        for transaction in self._transactions:
            if exc_type is None:
                await transaction.complete()
            else:
                await transaction.cancel()


@pytest.mark.asyncio
async def test_flush_chat_room_messages_persists_batch_and_returns_runtime_ids() -> None:
    gateway = InMemoryMessageCommandGateway()
    composition = FlushChatRoomMessagesComposition(
        message_commands=gateway,
        message_service=MessageService(
            encrypter=lambda value: f"enc:{value}".encode("utf-8")
        ),
        unit_of_work=StubUnitOfWork(),
    )

    response = await composition(
        FlushChatRoomMessagesRequest(
            messages=[
                ChatMessage(
                    chat_id=ChatId(UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")),
                    content="Hello",
                    created_at=datetime(2026, 4, 12, tzinfo=UTC),
                    author_kind=MessageAuthorKind.USER,
                    runtime_id="runtime-1",
                    author_id=ActorId(UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")),
                    author_display_name="Alice",
                )
            ]
        )
    )

    assert response.persisted_runtime_ids == ["runtime-1"]
    assert len(gateway.saved_messages) == 1
    assert gateway.saved_messages[0].author_kind is MessageAuthorKind.USER
    assert gateway.saved_messages[0].content == b"enc:Hello"
    assert gateway.saved_messages[0].runtime_id == "runtime-1"
