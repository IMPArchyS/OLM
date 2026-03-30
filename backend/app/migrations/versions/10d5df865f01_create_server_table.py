"""create_server_table

Revision ID: 10d5df865f01
Revises: b0a0a3429377
Create Date: 2026-03-30 12:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '10d5df865f01'
down_revision: Union[str, Sequence[str], None] = 'b0a0a3429377'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('server',
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('ip_address', sa.String(), nullable=False),
    sa.Column('api_domain', sa.String(), nullable=False),
    sa.Column('port', sa.Integer(), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('available', sa.Boolean(), nullable=False),
    sa.Column('production', sa.Boolean(), nullable=False),
    sa.Column('enabled', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('modified_at', sa.DateTime(), nullable=False),
    sa.Column('deleted_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_server_api_domain'), 'server', ['api_domain'], unique=True)
    op.create_index(op.f('ix_server_ip_address'), 'server', ['ip_address'], unique=True)
    op.create_index(op.f('ix_server_name'), 'server', ['name'], unique=False)
    op.create_index(op.f('ix_server_port'), 'server', ['port'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_server_port'), table_name='server')
    op.drop_index(op.f('ix_server_name'), table_name='server')
    op.drop_index(op.f('ix_server_ip_address'), table_name='server')
    op.drop_index(op.f('ix_server_api_domain'), table_name='server')
    op.drop_table('server')
