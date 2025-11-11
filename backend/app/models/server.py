from datetime import datetime
from typing import TYPE_CHECKING, List
from sqlmodel import Field, Relationship, SQLModel
from app.models.utils import now

if TYPE_CHECKING:
    from app.models.device import Device, DevicePublic
    from app.models.experiment import Experiment


class ServerBase(SQLModel):
    name: str = Field(index=True)
    ip_address: str = Field(index=True, unique=True)
    api_domain: str = Field(index=True, unique=True)
    websocket_port: int = Field(index=True, unique=True)


class Server(ServerBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    available: bool = Field(default=False)
    production: bool = Field(default=False)
    enabled: bool = Field(default=False)
    created_at: datetime = Field(default_factory=now)
    modified_at: datetime = Field(default_factory=now)
    deleted_at: datetime | None = Field(default=None)
    # Relationships
    devices: List["Device"] = Relationship(back_populates="server")
    experiments: List["Experiment"] = Relationship(back_populates="server")


class ServerCreate(ServerBase):
    pass


class ServerPublic(ServerBase):
    id: int
    available: bool 
    production: bool 
    enabled: bool
    created_at: datetime 
    modified_at: datetime 
    deleted_at: datetime | None


class ServerPubDetailed(ServerPublic):
    devices: List["DevicePublic"] = []
    experiments: List["Experiment"] = []


class ServerUpdate(SQLModel):
    name: str | None = None
    ip_address: str | None = None
    api_domain: str | None = None
    websocket_port: int | None = None  
    available: bool | None = None
    production: bool | None = None 
    enabled: bool | None = None 