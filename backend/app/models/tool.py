from typing import TYPE_CHECKING, List, Optional
from sqlmodel import Field, Relationship, SQLModel


if TYPE_CHECKING:
    from .workspace import Workspace
    from .reservation import Reservation


class Tool(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    occupied: bool = Field(default=False)
    # relationships
    workspace_id: Optional[int] = Field(default=None, foreign_key="workspace.id")
    workspace: Optional["Workspace"] = Relationship(back_populates="tools")
    reservations: List["Reservation"] = Relationship(back_populates="tool")
