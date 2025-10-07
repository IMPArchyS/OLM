from datetime import datetime
from typing import TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel

from app.models.utils import now

if TYPE_CHECKING:
    from app.models.software import Software
    from app.models.reserved_experiment import ReservedExperiment
    from app.models.device_type import DeviceType


class SchemaBase(SQLModel):
    name: str = Field(index=True, unique=True)
    note: str = Field(default=None, index=True)


class Schema(SchemaBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    
    created_at: datetime = Field(default_factory=now)
    modified_at: datetime = Field(default_factory=now)
    deleted_at: datetime | None = Field(default=None)
    # relationships
    software_id: int = Field(foreign_key="software.id")
    software: "Software" = Relationship(back_populates="schemas")
    
    device_types: list["DeviceType"] = Relationship(back_populates="schema_obj", cascade_delete=True)
    reserved_experiments: list["ReservedExperiment"] = Relationship(back_populates="schema_obj", cascade_delete=True)


class SchemaCreate(SchemaBase):
    pass


class SchemaPublic(SchemaBase):
    id: int 
    created_at: datetime
    modified_at: datetime
    deleted_at: datetime | None


class SchemaUpdate(SchemaBase):
    software_id: int