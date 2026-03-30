"""create_device_software_table

Revision ID: 60ea07f20b63
Revises: 50d67c89d013
Create Date: 2026-03-30 12:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '60ea07f20b63'
down_revision: Union[str, Sequence[str], None] = '50d67c89d013'
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
