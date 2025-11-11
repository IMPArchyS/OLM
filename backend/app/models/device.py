from datetime import datetime, time
from typing import TYPE_CHECKING, List
from sqlmodel import Field, Relationship, SQLModel
from app.models.device_type import DeviceTypePublic
from app.models.utils import now
from app.models.device_software import DeviceSoftware

if TYPE_CHECKING:
    from app.models.reserved_experiment import ReservedExperiment
    from app.models.software import Software
    from app.models.device_type import DeviceType
    from app.models.server import Server
    from app.models.experiment import Experiment
    from app.models.reservation import Reservation


class DeviceBase(SQLModel):
    name: str = Field(index=True)
    maintenance_start: time | None = Field(default=None)
    maintenance_end: time | None = Field(default=None)


class Device(DeviceBase, table=True):
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
    experiments: List["Experiment"] = Relationship(back_populates="device", cascade_delete=True)
    reserved_experiments: List["ReservedExperiment"] = Relationship(back_populates="device", cascade_delete=True)
    reservations: List["Reservation"] = Relationship(back_populates="device", cascade_delete=True)


class DeviceCreate(DeviceBase):
    pass


class DevicePublic(DeviceBase):
    id: int
    created_at: datetime
    modified_at: datetime
    deleted_at: datetime | None
    device_type: DeviceTypePublic


class DeviceUpdate(SQLModel):
    name: str | None = None
    maintenance_start: time | None = None
    maintenance_end: time | None = None
    device_type_id: int | None = None
    server_id: int | None = None