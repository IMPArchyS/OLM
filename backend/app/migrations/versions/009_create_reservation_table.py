"""create_reservation_table

Revision ID: 009_create_reservation_table
Revises: 008_create_experiment_table
Create Date: 2026-03-30 12:17:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '009_create_reservation_table'
down_revision: Union[str, Sequence[str], None] = '008_create_experiment_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('reservation',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('modified_at', sa.DateTime(), nullable=False),
    sa.Column('device_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['device_id'], ['device.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('reservation')
