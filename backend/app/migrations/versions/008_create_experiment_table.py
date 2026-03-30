"""create_experiment_table

Revision ID: 008_create_experiment_table
Revises: 007_create_device_software_table
Create Date: 2026-03-30 12:16:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '008_create_experiment_table'
down_revision: Union[str, Sequence[str], None] = '007_create_device_software_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('experiment',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('commands', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('input_arguments', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('output_arguments', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('modified_at', sa.DateTime(), nullable=False),
    sa.Column('deleted_at', sa.DateTime(), nullable=True),
    sa.Column('device_id', sa.Integer(), nullable=True),
    sa.Column('software_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['device_id'], ['device.id'], ),
    sa.ForeignKeyConstraint(['software_id'], ['software.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('experiment')
