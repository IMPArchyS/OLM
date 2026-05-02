from datetime import datetime
from typing import TYPE_CHECKING
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel
from app.models.utils import now

if TYPE_CHECKING:
    from app.models.device import Device


class ReservationBase(SQLModel):
    start: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    end: datetime = Field(sa_column=Column(DateTime(timezone=True)))

class Reservation(ReservationBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field()
    
    created_at: datetime = Field(default_factory=now)
    modified_at: datetime = Field(default_factory=now)
    # relationships
    device_id: int = Field(foreign_key="device.id")
    device: "Device" = Relationship(back_populates="reservations")


class ReservationCreate(ReservationBase):
    device_id: int


class ReservationPublic(ReservationBase):
    id: int 
    user_id: int
    device_id: int
    created_at: datetime
    modified_at: datetime 


class ReservationUpdate(SQLModel):
    start: datetime | None = None
    end: datetime | None = None
    device_id: int | None = None
    user_id: int | None = None


class ReservationWithUsername(ReservationPublic):
    username: str