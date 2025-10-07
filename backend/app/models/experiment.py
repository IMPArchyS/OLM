from datetime import datetime
from typing import TYPE_CHECKING, Any
from sqlmodel import JSON, Field, Relationship, SQLModel

from app.models.utils import now

if TYPE_CHECKING:
    from app.models.server import Server
    from app.models.device_type import DeviceType
    from app.models.software import Software
    from app.models.device import Device
    from app.models.reserved_experiment import ReservedExperiment

class ExperimentBase(SQLModel):
    commands: dict[str, Any] | None = Field(default=None, sa_type=JSON)
    experiment_commands: dict[str, Any] | None = Field(default=None, sa_type=JSON)
    output_arguments: dict[str, Any] | None = Field(default=None, sa_type=JSON)


class Experiment(ExperimentBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    
    has_schema: bool = Field(default=False, index=True)
    created_at: datetime = Field(default_factory=now)
    modified_at: datetime = Field(default_factory=now)
    deleted_at: datetime | None = Field(default=None)
    # Relationships
    server_id: int = Field(foreign_key="server.id")
    server: "Server" = Relationship(back_populates="experiments")
    
    device_type_id: int | None = Field(default=None, foreign_key="device_type.id")
    device_type: "DeviceType" = Relationship(back_populates="experiments")
    
    device_id: int | None = Field(default=None, foreign_key="device.id")
    device: "Device" = Relationship(back_populates="experiments")
    
    software_id: int | None = Field(default=None, foreign_key="software.id")
    software: "Software" = Relationship(back_populates="experiments")

    reserved_experiments: list["ReservedExperiment"] = Relationship(back_populates="experiment", cascade_delete=True)


class ExperimentCreate(ExperimentBase):
    pass