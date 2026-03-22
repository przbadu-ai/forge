"""add_skill_directories_and_skill_content

Revision ID: 0011_add_skill_directories_and_skill_content
Revises: 37f1742a38bd
Create Date: 2026-03-22 04:37:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0011_add_skill_directories_and_skill_content'
down_revision: Union[str, Sequence[str], None] = '37f1742a38bd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add skill_directories to app_settings and content/source_path to skill."""
    with op.batch_alter_table('app_settings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('skill_directories', sa.TEXT(), nullable=True))

    with op.batch_alter_table('skill', schema=None) as batch_op:
        batch_op.add_column(sa.Column('content', sa.TEXT(), nullable=True))
        batch_op.add_column(sa.Column('source_path', sa.TEXT(), nullable=True))


def downgrade() -> None:
    """Remove skill_directories from app_settings and content/source_path from skill."""
    with op.batch_alter_table('skill', schema=None) as batch_op:
        batch_op.drop_column('source_path')
        batch_op.drop_column('content')

    with op.batch_alter_table('app_settings', schema=None) as batch_op:
        batch_op.drop_column('skill_directories')
