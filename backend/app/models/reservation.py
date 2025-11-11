from datetime import datetime
from typing import TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel
from app.models.utils import now

if TYPE_CHECKING:
    from app.models.device import Device


class ReservationBase(SQLModel):
    start: datetime = Field()
    end: datetime = Field()
    queued: bool = Field(default=False)

class Reservation(ReservationBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    
    created_at: datetime = Field(default_factory=now)
    modified_at: datetime = Field(default_factory=now)
    # relationships
    device_id: int | None = Field(default=None, foreign_key="device.id")
    device: "Device" = Relationship(back_populates="reservations")


class ReservationCreate(ReservationBase):
    device_id: int


class ReservationQueue(SQLModel):
    device_id: int
    simulation_time: int
    timezone: str


class ReservationPublic(ReservationBase):
    id: int 
    created_at: datetime
    modified_at: datetime 


class ReservationUpdate(SQLModel):
    start: datetime | None = None
    end: datetime | None = None
    device_id: int | None = None