"""add mcp_server table

Revision ID: 0007_add_mcp_server
Revises: 0006_add_trace_data
Create Date: 2026-03-21

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007_add_mcp_server"
down_revision: Union[str, Sequence[str], None] = "0006_add_trace_data"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "mcp_server",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("command", sa.String(length=500), nullable=False),
        sa.Column("args", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("env_vars", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_mcp_server_name", "mcp_server", ["name"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_mcp_server_name", table_name="mcp_server")
    op.drop_table("mcp_server")
