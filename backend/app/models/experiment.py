from datetime import datetime
from datetime import time
from typing import TYPE_CHECKING, Any
from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy.dialects.postgresql import JSONB

from app.models.server import ServerExperiment
from app.models.software import SoftwarePublic
from app.models.utils import now

if TYPE_CHECKING:
    from app.models.server import Server
    from app.models.device_type import DeviceType
    from app.models.software import Software
    from app.models.device import Device
    from app.models.experiment_log import ExperimentLog


class ExperimentDevicePublic(SQLModel):
    id: int
    name: str
    maintenance_start: time | None = None
    maintenance_end: time | None = None


class ExperimentBase(SQLModel):
    commands: list[str] | None = Field(default=None, sa_type=JSONB)
    input_arguments: dict[str, Any] | None = Field(default=None, sa_type=JSONB)
    output_arguments: list[str] | None = Field(default=None, sa_type=JSONB)


class Experiment(ExperimentBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    
    device_remote_id: int | None = Field(default=None)
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
    
    experiment_logs: list["ExperimentLog"] = Relationship(back_populates="experiment", cascade_delete=True)


class ExperimentCreate(ExperimentBase):
    server_id: int


class ExperimentPublic(ExperimentBase):
    id: int
    server: ServerExperiment
    device: ExperimentDevicePublic
    software: SoftwarePublic


class ExperimentUpdate(ExperimentBase):
    server_id: int | None = None 
    device_type_id: int | None = None 
    device_id: int | None = None 
    software_id: int | None = None 