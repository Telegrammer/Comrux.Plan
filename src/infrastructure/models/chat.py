from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .chat_membership import ChatMembership
from .message import Message


class Chat(Base):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    context_kind: Mapped[str] = mapped_column(String(50), nullable=False)
    context_external_id: Mapped[str] = mapped_column(String(255), nullable=False)

    members: Mapped[list[ChatMembership]] = relationship(
        back_populates="chat",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    messages: Mapped[list[Message]] = relationship(
        back_populates="chat",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    __table_args__ = (UniqueConstraint("context_kind", "context_external_id"),)
