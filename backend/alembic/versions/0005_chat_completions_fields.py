"""add chat completions fields and app_settings table

Revision ID: 0005_chat_completions_fields
Revises: 100955aaddd5
Create Date: 2026-03-21

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005_chat_completions_fields"
down_revision: Union[str, Sequence[str], None] = "100955aaddd5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add new columns to conversation table
    with op.batch_alter_table("conversation", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("system_prompt", sqlmodel.sql.sqltypes.AutoString(), nullable=True)
        )
        batch_op.add_column(sa.Column("temperature", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("max_tokens", sa.Integer(), nullable=True))

    # Create app_settings table
    op.create_table(
        "app_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("system_prompt", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("temperature", sa.Float(), nullable=False),
        sa.Column("max_tokens", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("app_settings")

    with op.batch_alter_table("conversation", schema=None) as batch_op:
        batch_op.drop_column("max_tokens")
        batch_op.drop_column("temperature")
        batch_op.drop_column("system_prompt")
