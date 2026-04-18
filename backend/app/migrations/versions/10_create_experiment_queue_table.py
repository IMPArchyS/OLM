"""create_experiment_queue_table

Revision ID: 10_create_exp_queue_tbl
Revises: 09_create_experiment_device_tbl
Create Date: 2026-04-14 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "10_create_exp_queue_tbl"
down_revision: Union[str, Sequence[str], None] = "09_create_experiment_device_tbl"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "experiment_queue",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("server_id", sa.Integer(), nullable=False),
        sa.Column("experiment_log_id", sa.Integer(), nullable=False),
        sa.Column("experiment_id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.String(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_attempt_at", sa.DateTime(), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "not_started",
                "pending",
                "finished",
                "failed",
                name="queuestatus",
                native_enum=False,
            ),
            nullable=False,
            server_default="not_started",
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("modified_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["device_id"], ["device.id"]),
        sa.ForeignKeyConstraint(["experiment_id"], ["experiment.id"]),
        sa.ForeignKeyConstraint(["experiment_log_id"], ["experiment_log.id"]),
        sa.ForeignKeyConstraint(["server_id"], ["server.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_experiment_queue_status", "experiment_queue", ["status"], unique=False)
    op.create_index(
        "ix_experiment_queue_status_next_attempt_at",
        "experiment_queue",
        ["status", "next_attempt_at"],
        unique=False,
    )
    op.create_index("uq_experiment_queue_job_id", "experiment_queue", ["job_id"], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("uq_experiment_queue_job_id", table_name="experiment_queue")
    op.drop_index("ix_experiment_queue_status_next_attempt_at", table_name="experiment_queue")
    op.drop_index("ix_experiment_queue_status", table_name="experiment_queue")
    op.drop_table("experiment_queue")
