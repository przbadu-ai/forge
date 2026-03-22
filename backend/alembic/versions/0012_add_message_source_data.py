"""add source_data column to message table

Revision ID: 0012_add_message_source_data
Revises: 0011_add_skill_directories_and_skill_content
Create Date: 2026-03-22

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0012_add_message_source_data"
down_revision: Union[str, Sequence[str], None] = "0011_add_skill_directories_and_skill_content"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("message") as batch_op:
        batch_op.add_column(sa.Column("source_data", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("message") as batch_op:
        batch_op.drop_column("source_data")
