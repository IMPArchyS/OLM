from datetime import datetime
from typing import TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel

from app.models.utils import now

if TYPE_CHECKING:
    from app.models.argument import Argument


class OptionBase(SQLModel):
    name: str = Field(index=True, unique=True)
    value: str = Field(default=None, index=True)
    output_value: str = Field(default=None, index=True)


class Option(OptionBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    
    created_at: datetime = Field(default_factory=now)
    modified_at: datetime = Field(default_factory=now)
    # relationships
    argument_id: int | None = Field(default=None, foreign_key="argument.id")
    argument: "Argument" = Relationship(back_populates="options")


class OptionCreate(OptionBase):
    pass


class OptionPublic(OptionBase):
    id: int
    created_at: datetime
    modified_at: datetime
    argument_id: int


class OptionUpdate(OptionBase):
    argument_id: int | None = None