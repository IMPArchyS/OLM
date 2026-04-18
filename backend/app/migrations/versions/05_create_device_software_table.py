"""create_device_software_table

Revision ID: 05_create_device_software_table
Revises: 04_create_device_table
Create Date: 2026-03-30 12:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '05_create_device_software_table'
down_revision: Union[str, Sequence[str], None] = '04_create_device_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('device_software',
    sa.Column('device_id', sa.Integer(), nullable=False),
    sa.Column('software_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['device_id'], ['device.id'], ),
    sa.ForeignKeyConstraint(['software_id'], ['software.id'], ),
    sa.PrimaryKeyConstraint('device_id', 'software_id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('device_software')
