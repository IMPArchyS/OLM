from datetime import datetime
from typing import TYPE_CHECKING, List
from pydantic import BaseModel, ConfigDict
from sqlmodel import Field, Relationship, SQLModel
from app.models.utils import now
from app.models.schema import Schema

if TYPE_CHECKING:
    from app.models.device import Device


class DeviceTypeBase(SQLModel):
    name: str = Field(index=True, unique=True)


class DeviceType(DeviceTypeBase, table=True):
    __tablename__ = "device_type" # type: ignore
    
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=now)
    modified_at: datetime = Field(default_factory=now)
    # Relationships
    devices: List["Device"] = Relationship(back_populates="device_type", cascade_delete=True)
    schemas: List["Schema"] = Relationship(back_populates="device_type", cascade_delete=True)


class DeviceTypeCreate(DeviceTypeBase):
    pass


class DeviceTypePublic(DeviceTypeBase):
    id: int


class DeviceTypeUpdate(DeviceTypeBase):
    pass 


class DeviceTypeSyncPayload(BaseModel):
    name: str