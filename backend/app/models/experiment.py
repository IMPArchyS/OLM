from enum import Enum
from datetime import datetime
from datetime import time
from typing import TYPE_CHECKING, Any, TypedDict
from pydantic import model_validator
from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy.dialects.postgresql import JSONB

from app.models.experiment_device import ExperimentDevice
from app.models.software import SoftwarePublic
from app.models.utils import now

if TYPE_CHECKING:
    from app.models.software import Software
    from app.models.device import Device
    from app.models.experiment_log import ExperimentLog


class Command(str, Enum):
    INIT = "init"
    START = "start"
    CHANGE = "change"
    STOP = "stop"


class SoftwareName(str, Enum):
    OPENLOOP = "openloop"
    MATLAB = "matlab"
    SCILAB = "scilab"
    OPENMODELICA = "openmodelica"


class Step(TypedDict):
    duration: float 
    value: float 


class StepSequence(TypedDict):
    start_value: float
    steps: list[Step]


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

    created_at: datetime = Field(default_factory=now)
    modified_at: datetime = Field(default_factory=now)
    deleted_at: datetime | None = Field(default=None)
    # Relationships
    devices: list["Device"] = Relationship(back_populates="experiments", link_model=ExperimentDevice)
    
    software_id: int | None = Field(default=None, foreign_key="software.id")
    software: "Software" = Relationship(back_populates="experiments")
    
    experiment_logs: list["ExperimentLog"] = Relationship(back_populates="experiment", cascade_delete=True)


class ExperimentCreate(ExperimentBase):
    device_ids: list[int] | None = None


class ExperimentPublic(ExperimentBase):
    id: int
    devices: list[ExperimentDevicePublic] = []
    software: SoftwarePublic


class ExperimentUpdate(ExperimentBase):
    device_ids: list[int] | None = None
    software_id: int | None = None 

    
class ExperimentQueue(SQLModel):
    id: int
    user_id: int
    command: Command
    setpoint_changes: StepSequence | None
    input_arguments: dict[str, Any]
    output_arguments: list[str]
    simulation_time: int
    sample_rate: int 
    software_name: SoftwareName
    device_id: int
    schema_id: int | None
    
    @model_validator(mode="before")
    @classmethod
    def empty_setpoint_to_none(cls, values):
        if values.get("setpoint_changes") == {}:
            values["setpoint_changes"] = None
        return values
