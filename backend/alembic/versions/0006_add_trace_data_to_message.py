"""add trace_data column to message table

Revision ID: 0006_add_trace_data
Revises: 0005_chat_completions_fields
Create Date: 2026-03-21

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0006_add_trace_data"
down_revision: Union[str, Sequence[str], None] = "0005_chat_completions_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("message") as batch_op:
        batch_op.add_column(sa.Column("trace_data", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("message") as batch_op:
        batch_op.drop_column("trace_data")
