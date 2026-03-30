from datetime import datetime, time
from typing import TYPE_CHECKING, List
from pydantic import BaseModel, ConfigDict, Field as PydanticField, model_validator
from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint
from app.models.device_type import DeviceTypePublic, DeviceTypeSyncPayload
from app.models.software import SoftwarePublic, SoftwareSyncPayload
from app.models.utils import now
from app.models.device_software import DeviceSoftware
from app.models.experiment_device import ExperimentDevice

if TYPE_CHECKING:
    from app.models.software import Software
    from app.models.device_type import DeviceType
    from app.models.server import Server
    from app.models.experiment import Experiment
    from app.models.experiment_log import ExperimentLog
    from app.models.reservation import Reservation


class DeviceBase(SQLModel):
    name: str = Field(index=True)
    maintenance_start: time | None = Field(default=None)
    maintenance_end: time | None = Field(default=None)


class Device(DeviceBase, table=True):
    __table_args__ = (UniqueConstraint("server_id", "name", name="uq_device_server_name"),)
    id: int | None = Field(default=None, primary_key=True)

    created_at: datetime = Field(default_factory=now)
    modified_at: datetime = Field(default_factory=now)
    deleted_at: datetime | None = Field(default=None)
    # Relationships
    device_type_id: int = Field(foreign_key="device_type.id")
    device_type: "DeviceType" = Relationship(back_populates="devices")
    
    server_id: int = Field(foreign_key="server.id")
    server: "Server" = Relationship(back_populates="devices")
    
    softwares: List["Software"] = Relationship(back_populates="devices", link_model=DeviceSoftware)
    experiments: List["Experiment"] = Relationship(back_populates="devices", link_model=ExperimentDevice)
    experiment_logs: List["ExperimentLog"] = Relationship(back_populates="device")
    reservations: List["Reservation"] = Relationship(back_populates="device", cascade_delete=True)


class DeviceCreate(DeviceBase):
    device_type_id: int
    server_id: int


class DevicePublic(DeviceBase):
    id: int
    created_at: datetime
    modified_at: datetime
    deleted_at: datetime | None
    device_type: DeviceTypePublic
    softwares: list[SoftwarePublic]


class DeviceUpdate(SQLModel):
    name: str | None = None
    maintenance_start: time | None = None
    maintenance_end: time | None = None
    device_type_id: int | None = None
    server_id: int | None = None


class DeviceWithSoftware(DeviceBase):
    id: int
    deleted_at: datetime | None
    device_type: DeviceTypePublic
    softwares: list[SoftwarePublic]


class DeviceSyncPayload(BaseModel):
    name: str
    device_type: DeviceTypeSyncPayload
    maintenance_start: time | None = None
    maintenance_end: time | None = None
    software: list[SoftwareSyncPayload] = PydanticField(default_factory=list)

    @model_validator(mode="after")
    def validate_maintenance_window(self):
        if self.maintenance_start and self.maintenance_end and self.maintenance_start > self.maintenance_end:
            raise ValueError("maintenance_start cannot be after maintenance_end")
        return self