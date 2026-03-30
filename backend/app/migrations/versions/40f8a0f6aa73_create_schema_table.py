"""create_schema_table

Revision ID: 40f8a0f6aa73
Revises: 30c4c6cf9c2e
Create Date: 2026-03-30 12:13:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '40f8a0f6aa73'
down_revision: Union[str, Sequence[str], None] = '30c4c6cf9c2e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('schema',
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('note', sa.String(), nullable=False),
    sa.Column('schema_type', sa.Enum('control', 'ident', name='schematype'), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('modified_at', sa.DateTime(), nullable=False),
    sa.Column('deleted_at', sa.DateTime(), nullable=True),
    sa.Column('software_id', sa.Integer(), nullable=False),
    sa.Column('device_type_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['device_type_id'], ['device_type.id'], ),
    sa.ForeignKeyConstraint(['software_id'], ['software.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_schema_name'), 'schema', ['name'], unique=True)
    op.create_index(op.f('ix_schema_note'), 'schema', ['note'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_schema_note'), table_name='schema')
    op.drop_index(op.f('ix_schema_name'), table_name='schema')
    op.drop_table('schema')
    sa.Enum('control', 'ident', name='schematype').drop(op.get_bind(), checkfirst=True)
