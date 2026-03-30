"""create_argument_table

Revision ID: 50d67c89d013
Revises: 40f8a0f6aa73
Create Date: 2026-03-30 12:14:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '50d67c89d013'
down_revision: Union[str, Sequence[str], None] = '40f8a0f6aa73'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('argument',
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('label', sa.String(), nullable=False),
    sa.Column('default_value', sa.String(), nullable=False),
    sa.Column('row', sa.Integer(), nullable=False),
    sa.Column('order', sa.Integer(), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('modified_at', sa.DateTime(), nullable=False),
    sa.Column('schema_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['schema_id'], ['schema.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_argument_default_value'), 'argument', ['default_value'], unique=False)
    op.create_index(op.f('ix_argument_label'), 'argument', ['label'], unique=False)
    op.create_index(op.f('ix_argument_name'), 'argument', ['name'], unique=True)
    op.create_index(op.f('ix_argument_order'), 'argument', ['order'], unique=False)
    op.create_index(op.f('ix_argument_row'), 'argument', ['row'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_argument_row'), table_name='argument')
    op.drop_index(op.f('ix_argument_order'), table_name='argument')
    op.drop_index(op.f('ix_argument_name'), table_name='argument')
    op.drop_index(op.f('ix_argument_label'), table_name='argument')
    op.drop_index(op.f('ix_argument_default_value'), table_name='argument')
    op.drop_table('argument')
