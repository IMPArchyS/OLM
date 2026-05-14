from datetime import datetime
from typing import TYPE_CHECKING, Any, List
from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel, Column
from app.models.utils import now

if TYPE_CHECKING:
    from app.models.device import Device


class AnimationTarget(SQLModel):
    mesh: str
    type: str                    
    color: list[float]           
    axis: str | None = None      
    offset: float | None = None  
    abs: bool | None = None      


class ModelConfig(SQLModel):
    model_file: str                              
    animations: dict[str, AnimationTarget]       


class DeviceTypeBase(SQLModel):
    name: str = Field(index=True, unique=True)


class DeviceType(DeviceTypeBase, table=True):
    __tablename__ = "device_type" # type: ignore
    
    id: int | None = Field(default=None, primary_key=True)
    visual_config: dict[str, Any] | None = Field(default=None, sa_column=Column(JSONB, nullable=True))
    created_at: datetime = Field(default_factory=now)
    modified_at: datetime = Field(default_factory=now)
    # Relationships
    devices: List["Device"] = Relationship(back_populates="device_type", cascade_delete=True)


class DeviceTypePublic(DeviceTypeBase):
    id: int
    visual_config: dict[str, Any] | None


class DeviceTypeSyncPayload(BaseModel):
    name: str