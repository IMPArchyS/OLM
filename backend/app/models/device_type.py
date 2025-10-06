from datetime import datetime
from typing import TYPE_CHECKING, List
from sqlmodel import Field, Relationship, SQLModel
from app.models.utils import now

if TYPE_CHECKING:
    from app.models.device import Device
    from app.models.experiment import Experiment


class DeviceType(SQLModel, table=True):
    __tablename__ = "device_type" # type: ignore
    
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    created_at: datetime = Field(default_factory=now)
    modified_at: datetime = Field(default_factory=now)
    # Relationships
    devices: List["Device"] = Relationship(back_populates="device_type")
    experiments: List["Experiment"] = Relationship(back_populates="device_type")