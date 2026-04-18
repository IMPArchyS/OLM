"""create_device_table

Revision ID: 04_create_device_table
Revises: 03_create_software_table
Create Date: 2026-03-30 12:12:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '04_create_device_table'
down_revision: Union[str, Sequence[str], None] = '03_create_software_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('device',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('maintenance_start', sa.Time(), nullable=True),
    sa.Column('maintenance_end', sa.Time(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('modified_at', sa.DateTime(), nullable=False),
    sa.Column('deleted_at', sa.DateTime(), nullable=True),
    sa.Column('device_type_id', sa.Integer(), nullable=False),
    sa.Column('server_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['device_type_id'], ['device_type.id'], ),
    sa.ForeignKeyConstraint(['server_id'], ['server.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('server_id', 'name', name='uq_device_server_name')
    )
    op.create_index(op.f('ix_device_name'), 'device', ['name'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_device_name'), table_name='device')
    op.drop_table('device')
