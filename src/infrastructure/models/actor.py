from uuid import UUID

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .chat_membership import ChatMembership


class Actor(Base):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    display_name: Mapped[str] = mapped_column(nullable=False)
    public_id: Mapped[str] = mapped_column(nullable=False, unique=True)

    memberships: Mapped[list[ChatMembership]] = relationship(
        back_populates="actor",
        lazy="selectin",
    )
