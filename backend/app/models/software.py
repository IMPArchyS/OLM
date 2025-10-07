from datetime import datetime
from typing import TYPE_CHECKING, List
from sqlmodel import Field, Relationship, SQLModel
from app.models.utils import now
from app.models.device_software import DeviceSoftware

if TYPE_CHECKING:
    from app.models.device import Device
    from app.models.experiment import Experiment
    from app.models.schema import Schema


class Software(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    created_at: datetime = Field(default_factory=now)
    modified_at: datetime = Field(default_factory=now)
    # relationships
    devices: List["Device"] = Relationship(back_populates="softwares", link_model=DeviceSoftware)
    experiments: List["Experiment"] = Relationship(back_populates="software")
    schemas: List["Schema"] = Relationship(back_populates="software")