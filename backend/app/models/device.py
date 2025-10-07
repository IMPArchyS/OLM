from datetime import datetime
from typing import TYPE_CHECKING, List
from sqlmodel import Field, Relationship, SQLModel
from app.models.utils import now
from app.models.device_software import DeviceSoftware

if TYPE_CHECKING:
    from app.models.reserved_experiment import ReservedExperiment
    from app.models.software import Software
    from app.models.device_type import DeviceType
    from app.models.server import Server
    from app.models.experiment import Experiment


class DeviceBase(SQLModel):
    name: str = Field(index=True)


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


class DeviceCreate(DeviceBase):
    pass


class DevicePublic(DeviceBase):
    id: int
    created_at: datetime
    modified_at: datetime
    deleted_at: datetime | None


class DeviceUpdate(DeviceBase):
    device_type_id: int
    server_id: int