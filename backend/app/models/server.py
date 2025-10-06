from datetime import datetime
from typing import TYPE_CHECKING, List
from sqlmodel import Field, Relationship, SQLModel
from app.models.utils import now

if TYPE_CHECKING:
    from app.models.device import Device
    from app.models.experiment import Experiment

class Server(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    ip_address: str = Field(index=True, unique=True)
    api_domain: str = Field(index=True, unique=True)
    websocket_port: int = Field(index=True, unique=True)
    available: bool = Field(default=False)
    production: bool = Field(default=False)
    enabled: bool = Field(default=False)
    created_at: datetime = Field(default_factory=now)
    modified_at: datetime = Field(default_factory=now)
    deleted_at: datetime | None = Field(default=None)
    # Relationships
    devices: List["Device"] = Relationship(back_populates="server")
    experiments: List["Experiment"] = Relationship(back_populates="server")