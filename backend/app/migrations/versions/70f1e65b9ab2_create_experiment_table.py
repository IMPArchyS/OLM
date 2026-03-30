"""create_experiment_table

Revision ID: 70f1e65b9ab2
Revises: 60ea07f20b63
Create Date: 2026-03-30 12:16:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '70f1e65b9ab2'
down_revision: Union[str, Sequence[str], None] = '60ea07f20b63'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('experiment',
    sa.Column('commands', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('input_arguments', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('output_arguments', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('device_remote_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('modified_at', sa.DateTime(), nullable=False),
    sa.Column('deleted_at', sa.DateTime(), nullable=True),
    sa.Column('server_id', sa.Integer(), nullable=False),
    sa.Column('device_type_id', sa.Integer(), nullable=True),
    sa.Column('device_id', sa.Integer(), nullable=True),
    sa.Column('software_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['device_id'], ['device.id'], ),
    sa.ForeignKeyConstraint(['device_type_id'], ['device_type.id'], ),
    sa.ForeignKeyConstraint(['server_id'], ['server.id'], ),
    sa.ForeignKeyConstraint(['software_id'], ['software.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('experiment')
