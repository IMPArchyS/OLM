"""create_experiment_log_table

Revision ID: a0b7d4c1e9f8
Revises: 90a5e3f33d6b
Create Date: 2026-03-30 12:19:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a0b7d4c1e9f8'
down_revision: Union[str, Sequence[str], None] = '90a5e3f33d6b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('experiment_log',
    sa.Column('run', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('note', sa.String(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('modified_at', sa.DateTime(), nullable=False),
    sa.Column('deleted_at', sa.DateTime(), nullable=True),
    sa.Column('started_at', sa.DateTime(), nullable=False),
    sa.Column('finished_at', sa.DateTime(), nullable=True),
    sa.Column('stopped_at', sa.DateTime(), nullable=True),
    sa.Column('timedout_at', sa.DateTime(), nullable=True),
    sa.Column('experiment_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['experiment_id'], ['experiment.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_experiment_log_note'), 'experiment_log', ['note'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_experiment_log_note'), table_name='experiment_log')
    op.drop_table('experiment_log')
