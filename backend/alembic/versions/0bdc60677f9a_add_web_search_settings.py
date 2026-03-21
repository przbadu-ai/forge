"""add_web_search_settings

Revision ID: 0bdc60677f9a
Revises: 0010_add_embedding_settings
Create Date: 2026-03-21 23:56:17.549086

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = '0bdc60677f9a'
down_revision: Union[str, Sequence[str], None] = '0010_add_embedding_settings'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('app_settings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('searxng_base_url', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
        batch_op.add_column(sa.Column('exa_api_key_encrypted', sqlmodel.sql.sqltypes.AutoString(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('app_settings', schema=None) as batch_op:
        batch_op.drop_column('exa_api_key_encrypted')
        batch_op.drop_column('searxng_base_url')
