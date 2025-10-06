from datetime import datetime
from typing import TYPE_CHECKING, Any
from sqlmodel import Field, Relationship, SQLModel, JSON

from app.models.utils import now

if TYPE_CHECKING:
    from app.models.device import Device
    from app.models.experiment import Experiment
    from app.models.schema import Schema   
class ReservedExperiment(SQLModel, table=True):
    __tablename__ = "reserved_experiment" # type: ignore
    
    id: int | None = Field(default=None, primary_key=True)
    input: dict[str, Any] | None = Field(default=None, sa_type=JSON)
    output: dict[str, Any] | None = Field(default=None, sa_type=JSON)
    note: str | None = Field(default=None, index=True)
    simulation_time: int = Field()
    sampling_rate: int = Field()
    filled: bool = Field(default=False, index=True)
    remote_id: int | None = Field(default=None)
    created_at: datetime = Field(default_factory=now)
    modified_at: datetime = Field(default_factory=now)
    deleted_at: datetime | None = Field(default=None)
    # Relationships
    experiment_id: int = Field(foreign_key="experiment.id")
    experiment: "Experiment" = Relationship(back_populates="reserved_experiments")

    device_id: int = Field(foreign_key="device.id")
    device: "Device" = Relationship(back_populates="reserved_experiments")
    
    schema_id: int = Field(foreign_key="schema.id")
    schema_obj: "Schema" = Relationship(back_populates="reserved_experiments")