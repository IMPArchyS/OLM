from datetime import datetime
from typing import TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel

from app.models.utils import now

if TYPE_CHECKING:
    from app.models.option import Option
    from app.models.schema import Schema


class ArgumentBase(SQLModel):
    name: str = Field(index=True, unique=True)
    label: str = Field(default=None, index=True)
    default_value: str = Field(default=None, index=True)
    row: int = Field(default=None, index=True)
    order: int = Field(default=None, index=True)


class Argument(ArgumentBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    
    created_at: datetime = Field(default_factory=now)
    modified_at: datetime = Field(default_factory=now)
    # relationships
    schema_id: int | None = Field(default=None, foreign_key="schema.id")
    schema_obj: "Schema" = Relationship(back_populates="arguments")
    options: list["Option"] = Relationship(back_populates="argument", cascade_delete=True)


class ArgumentCreate(ArgumentBase):
    pass


class ArgumentPublic(ArgumentBase):
    id: int
    created_at: datetime
    modified_at: datetime
    schema_id: int


class ArgumentUpdate(ArgumentBase):
    schema_id: int | None = None