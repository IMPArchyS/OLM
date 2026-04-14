"""create_experiment_log_table

Revision ID: 011_create_experiment_log_table
Revises: 010_create_option_table
Create Date: 2026-03-30 12:19:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '011_create_experiment_log_table'
down_revision: Union[str, Sequence[str], None] = '010_create_option_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('experiment_log',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('run', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('note', sa.String(), nullable=True),
    sa.Column('started_at', sa.DateTime(), nullable=True),
    sa.Column('finished_at', sa.DateTime(), nullable=True),
    sa.Column(
        'finish_reason',
        sa.Enum(
            'n/a',
            'user_stop',
            'simulation_time_reached',
            'device_timeout',
            'exception_error',
            name='finishreason',
            native_enum=False,
        ),
        nullable=False,
        server_default='n/a',
    ),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('modified_at', sa.DateTime(), nullable=False),
    sa.Column('deleted_at', sa.DateTime(), nullable=True),
    sa.Column('experiment_id', sa.Integer(), nullable=False),
    sa.Column('device_id', sa.Integer(), nullable=False),
    sa.Column('server_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['experiment_id'], ['experiment.id'], ),
    sa.ForeignKeyConstraint(['device_id'], ['device.id'], ),
    sa.ForeignKeyConstraint(['server_id'], ['server.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_experiment_log_note'), 'experiment_log', ['note'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_experiment_log_note'), table_name='experiment_log')
    op.drop_table('experiment_log')
