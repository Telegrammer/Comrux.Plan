from datetime import UTC, datetime
from uuid import UUID

from domain.entities.actor import ActorId
from domain.entities.chat import ChatId
from domain.entities.message import Message, MessageAuthorKind, MessageId
from infrastructure.adapters.clock import TimestampClock
from infrastructure.adapters.mappers import SQLAlchemyDomainMessageMapper
from infrastructure.chat_session import RedisChatMessageDTO, RedisChatMessageMapper


def test_sqlalchemy_domain_message_mapper_normalizes_naive_datetime_to_utc() -> None:
    mapper = SQLAlchemyDomainMessageMapper()
    domain_message = Message(
        id=MessageId(None),
        runtime_id="runtime-1",
        chat_id=ChatId(UUID("11111111-1111-1111-1111-111111111111")),
        content=b"encrypted",
        created_at=datetime(2026, 4, 13, 18, 59, 15, 297120),
        author_kind=MessageAuthorKind.USER,
        author_id=ActorId(UUID("22222222-2222-2222-2222-222222222222")),
    )

    mapped_message = mapper.to_dto(domain_message)

    assert mapped_message.created_at.tzinfo is UTC
    assert mapped_message.created_at == datetime(
        2026,
        4,
        13,
        18,
        59,
        15,
        297120,
        tzinfo=UTC,
    )


def test_redis_chat_message_mapper_normalizes_naive_payload_datetime_to_utc() -> None:
    mapper = RedisChatMessageMapper()
    dto = RedisChatMessageDTO(
        runtime_id="runtime-1",
        chat_id="11111111-1111-1111-1111-111111111111",
        author_id="22222222-2222-2222-2222-222222222222",
        author_display_name="Alice",
        content="Hello",
        created_at="2026-04-13T18:59:15.297120",
        author_kind=MessageAuthorKind.USER.value,
    )

    message = mapper.to_message(dto)

    assert message.created_at.tzinfo is UTC
    assert message.created_at == datetime(
        2026,
        4,
        13,
        18,
        59,
        15,
        297120,
        tzinfo=UTC,
    )


def test_timestamp_clock_returns_utc_aware_datetime() -> None:
    clock = TimestampClock()

    current_time = clock.now()

    assert current_time.tzinfo is UTC
    assert isinstance(current_time, datetime)
