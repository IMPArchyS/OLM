from typing import TYPE_CHECKING, List
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .tool import Tool


class Workspace(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    # relationships
    tools: List["Tool"] = Relationship(back_populates="workspace")
