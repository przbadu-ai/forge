"""add embedding and reranker settings columns

Revision ID: 0010_add_embedding_settings
Revises: 0009_add_uploaded_file
Create Date: 2026-03-21

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0010_add_embedding_settings"
down_revision: Union[str, Sequence[str], None] = "0009_add_uploaded_file"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("app_settings") as batch_op:
        batch_op.add_column(sa.Column("embedding_base_url", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("embedding_model", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("reranker_base_url", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("reranker_model", sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("app_settings") as batch_op:
        batch_op.drop_column("reranker_model")
        batch_op.drop_column("reranker_base_url")
        batch_op.drop_column("embedding_model")
        batch_op.drop_column("embedding_base_url")
