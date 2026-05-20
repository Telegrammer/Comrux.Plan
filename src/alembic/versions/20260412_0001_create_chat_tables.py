"""create chat tables

Revision ID: 20260412_0001
Revises:
Create Date: 2026-04-12 00:01:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260412_0001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    author_kind = sa.Enum("USER", "BOT", "SYSTEM", name="messageauthorkind")

    op.create_table(
        "actors",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("public_id", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_actors")),
        sa.UniqueConstraint("public_id", name=op.f("uq_actors_public_id")),
    )

    op.create_table(
        "chats",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("context_kind", sa.String(length=50), nullable=False),
        sa.Column("context_external_id", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chats")),
        sa.UniqueConstraint(
            "context_kind",
            "context_external_id",
            name=op.f("uq_chats_context_kind_context_external_id"),
        ),
    )

    op.create_table(
        "chat_memberships",
        sa.Column("chat_id", sa.UUID(), nullable=False),
        sa.Column("actor_id", sa.UUID(), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["actors.id"],
            name=op.f("fk_chat_memberships_actor_id_actors"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["chat_id"],
            ["chats.id"],
            name=op.f("fk_chat_memberships_chat_id_chats"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "chat_id",
            "actor_id",
            name=op.f("pk_chat_memberships"),
        ),
    )

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.Column("chat_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("author_id", sa.UUID(), nullable=True),
        sa.Column("author_kind", author_kind, nullable=False),
        sa.Column("reply_to_message_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["actors.id"],
            name=op.f("fk_messages_author_id_actors"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["chat_id"],
            ["chats.id"],
            name=op.f("fk_messages_chat_id_chats"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["reply_to_message_id"],
            ["messages.id"],
            name=op.f("fk_messages_reply_to_message_id_messages"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_messages")),
    )
    op.create_index(op.f("ix_messages_chat_id"), "messages", ["chat_id"], unique=False)
    op.create_index(
        op.f("ix_messages_reply_to_message_id"),
        "messages",
        ["reply_to_message_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_messages_reply_to_message_id"), table_name="messages")
    op.drop_index(op.f("ix_messages_chat_id"), table_name="messages")
    op.drop_table("messages")
    op.drop_table("chat_memberships")
    op.drop_table("chats")
    op.drop_table("actors")
