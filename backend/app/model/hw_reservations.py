from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel


class Workspace(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    # relationships
    tools: List["Tool"] = Relationship(back_populates="workspaces")


class Tool(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    occupied: bool = Field(default=False)
    # relationships
    workspace_id: Optional[int] = Field(default=None, foreign_key="workspace.id")
    workspace: Optional["Workspace"] = Relationship(back_populates="tools")


class Reservation(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    start_time: str | None = None
    end_time: str | None = None
    # relationships
    user_id: int | None = None
    workspace_id: int = Field(foreign_key="workspace.id")
    workspace: "Workspace" = Relationship(back_populates="reservations")
    tool_id: int = Field(foreign_key="tool.id")
    tool: "Tool" = Relationship(back_populates="reservations")
