"""add runtime id to messages

Revision ID: 20260413_0002
Revises: 20260412_0001
Create Date: 2026-04-13 00:02:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260413_0002"
down_revision: str | None = "20260412_0001"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("messages", sa.Column("runtime_id", sa.String(length=64), nullable=True))
    op.create_index(op.f("ix_messages_runtime_id"), "messages", ["runtime_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_messages_runtime_id"), table_name="messages")
    op.drop_column("messages", "runtime_id")
