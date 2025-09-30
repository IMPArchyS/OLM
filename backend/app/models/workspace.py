from typing import TYPE_CHECKING, List, Optional
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .tool import Tool


class WorkspaceBase(SQLModel):
    name: str = Field(index=True)

class Workspace(WorkspaceBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    # relationships
    tools: List["Tool"] = Relationship(back_populates="workspace")

class WorkspaceCreate(WorkspaceBase):
    pass

class WorkspaceUpdate(SQLModel):
    name: Optional[str] = None