"""add schema types

Revision ID: 1882e6f81d2b
Revises: 4348d94628d3
Create Date: 2025-11-24 22:32:49.085049

"""
from typing import Sequence, Union

import sqlmodel
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '1882e6f81d2b'
down_revision: Union[str, Sequence[str], None] = '4348d94628d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the enum type first
    schema_type_enum = postgresql.ENUM('control', 'ident', name='schematype')
    schema_type_enum.create(op.get_bind(), checkfirst=True)
    
    # Then add the column
    op.add_column('schema', sa.Column('schema_type', sa.Enum('control', 'ident', name='schematype'), nullable=False, server_default='control'))


def downgrade() -> None:
    op.drop_column('schema', 'schema_type')
    # Drop the enum type
    schema_type_enum = postgresql.ENUM('control', 'ident', name='schematype')
    schema_type_enum.drop(op.get_bind(), checkfirst=True)