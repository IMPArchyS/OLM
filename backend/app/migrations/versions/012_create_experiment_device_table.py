"""create_experiment_device_table

Revision ID: 012_create_experiment_device_tbl
Revises: 011_create_experiment_log_table
Create Date: 2026-03-30 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "012_create_experiment_device_tbl"
down_revision: Union[str, Sequence[str], None] = "011_create_experiment_log_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "experiment_device",
        sa.Column("experiment_id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["experiment_id"], ["experiment.id"]),
        sa.ForeignKeyConstraint(["device_id"], ["device.id"]),
        sa.PrimaryKeyConstraint("experiment_id", "device_id"),
    )
    op.create_index(
        "ix_experiment_device_device_id",
        "experiment_device",
        ["device_id"],
        unique=False,
    )

    # Backfill current one-to-many relation into the new many-to-many table.
    op.execute(
        sa.text(
            """
            INSERT INTO experiment_device (experiment_id, device_id)
            SELECT id, device_id
            FROM experiment
            WHERE device_id IS NOT NULL
            ON CONFLICT DO NOTHING
            """
        )
    )

    with op.batch_alter_table("experiment") as batch_op:
        batch_op.drop_column("device_id")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("experiment") as batch_op:
        batch_op.add_column(sa.Column("device_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_experiment_device_id_device",
            "device",
            ["device_id"],
            ["id"],
        )

    # If multiple devices are associated, keep one deterministically for the legacy column.
    op.execute(
        sa.text(
            """
            UPDATE experiment e
            SET device_id = mapped.device_id
            FROM (
                SELECT experiment_id, MIN(device_id) AS device_id
                FROM experiment_device
                GROUP BY experiment_id
            ) AS mapped
            WHERE e.id = mapped.experiment_id
            """
        )
    )

    op.drop_index("ix_experiment_device_device_id", table_name="experiment_device")
    op.drop_table("experiment_device")
