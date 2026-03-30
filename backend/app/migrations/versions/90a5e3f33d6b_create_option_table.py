"""create_option_table

Revision ID: 90a5e3f33d6b
Revises: 80bc6b2ec7f4
Create Date: 2026-03-30 12:18:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '90a5e3f33d6b'
down_revision: Union[str, Sequence[str], None] = '80bc6b2ec7f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('option',
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('value', sa.String(), nullable=False),
    sa.Column('output_value', sa.String(), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('modified_at', sa.DateTime(), nullable=False),
    sa.Column('argument_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['argument_id'], ['argument.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_option_name'), 'option', ['name'], unique=True)
    op.create_index(op.f('ix_option_output_value'), 'option', ['output_value'], unique=False)
    op.create_index(op.f('ix_option_value'), 'option', ['value'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_option_value'), table_name='option')
    op.drop_index(op.f('ix_option_output_value'), table_name='option')
    op.drop_index(op.f('ix_option_name'), table_name='option')
    op.drop_table('option')
