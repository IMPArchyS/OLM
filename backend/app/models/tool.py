from typing import TYPE_CHECKING, List
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, mapped_column, Mapped
from app.core.config import Base

if TYPE_CHECKING:
    from app.models.workspace import Workspace
    from app.models.reservation import Reservation


class Tool(Base):
    __tablename__ = "tool"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(index=True)
    occupied: Mapped[bool] = mapped_column(default=False)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspace.id"))
    # relationships
    workspace: Mapped["Workspace"] = relationship(back_populates="tools")
    reservations: Mapped[List["Reservation"]] = relationship(back_populates="tool")