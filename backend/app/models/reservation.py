from typing import TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .tool import Tool


class Reservation(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    start_time: str | None = None
    end_time: str | None = None
    # relationships
    user_id: int | None = None
    tool_id: int = Field(foreign_key="tool.id")
    tool: "Tool" = Relationship(back_populates="reservations")
