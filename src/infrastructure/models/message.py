from __future__ import annotations

from typing import TYPE_CHECKING
from datetime import datetime
from uuid import UUID

from domain.entities.message import MessageAuthorKind
from sqlalchemy import DateTime, Enum, ForeignKey, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .actor import Actor
    from .chat import Chat


class Message(Base):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    runtime_id: Mapped[str | None] = mapped_column(nullable=True, unique=True, index=True)
    content: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    chat_id: Mapped[UUID] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    author_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("actors.id", ondelete="SET NULL"), nullable=True
    )
    author_kind: Mapped[MessageAuthorKind] = mapped_column(
        Enum(MessageAuthorKind), nullable=False
    )
    reply_to_message_id: Mapped[int | None] = mapped_column(
        ForeignKey("messages.id", ondelete="SET NULL"), nullable=True, index=True
    )
    chat: Mapped[Chat] = relationship(back_populates="messages")
    author: Mapped[Actor | None] = relationship(lazy="selectin")