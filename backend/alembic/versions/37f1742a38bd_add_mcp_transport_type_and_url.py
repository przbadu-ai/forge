"""add_mcp_transport_type_and_url

Revision ID: 37f1742a38bd
Revises: 0bdc60677f9a
Create Date: 2026-03-22 09:06:31.436852

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = '37f1742a38bd'
down_revision: Union[str, Sequence[str], None] = '0bdc60677f9a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add transport_type and url columns to mcp_server, make command nullable."""
    with op.batch_alter_table('mcp_server', schema=None) as batch_op:
        batch_op.add_column(sa.Column('transport_type', sa.VARCHAR(length=20), nullable=False, server_default='stdio'))
        batch_op.add_column(sa.Column('url', sa.VARCHAR(length=500), nullable=True))
        batch_op.alter_column('command',
               existing_type=sa.VARCHAR(length=500),
               nullable=True)


def downgrade() -> None:
    """Remove transport_type and url columns, make command non-nullable."""
    with op.batch_alter_table('mcp_server', schema=None) as batch_op:
        batch_op.alter_column('command',
               existing_type=sa.VARCHAR(length=500),
               nullable=False)
        batch_op.drop_column('url')
        batch_op.drop_column('transport_type')
