from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Column, Enum as SAEnum
from sqlmodel import Field, Relationship, SQLModel

from app.models.experiment import ExperimentQueuePayload
from app.models.experiment_log import PydanticJSONB
from app.models.utils import now

if TYPE_CHECKING:
    from app.models.experiment import Experiment
    from app.models.experiment_log import ExperimentLog


class QueueStatus(str, Enum):
    NOT_STARTED = "not_started"
    PENDING = "pending"
    FINISHED = "finished"
    FAILED = "failed"


class ExperimentQueue(SQLModel, table=True):
    __tablename__ = "experiment_queue" # type: ignore
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(nullable=False)
    device_id: int = Field(foreign_key="device.id")
    server_id: int = Field(foreign_key="server.id")
    experiment_log_id: int = Field(foreign_key="experiment_log.id")
    job_id: str | None = Field(default=None)
    attempts: int = Field(default=0)
    next_attempt_at: datetime | None = Field(default=None)
    payload: ExperimentQueuePayload = Field(sa_column=Column(PydanticJSONB, nullable=False))
    status: QueueStatus = Field(
        default=QueueStatus.NOT_STARTED,
        sa_column=Column(
            SAEnum(
                QueueStatus,
                values_callable=lambda enum_cls: [member.value for member in enum_cls],
                native_enum=False,
            ),
            nullable=False,
            server_default=QueueStatus.NOT_STARTED.value,
        ),
    )
    created_at: datetime = Field(default_factory=now)
    modified_at: datetime = Field(default_factory=now)
    # relationships
    experiment_id: int = Field(foreign_key="experiment.id")
    experiment: "Experiment" = Relationship(back_populates="experiment_queues")
    experiment_log: "ExperimentLog" = Relationship()