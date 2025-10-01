from typing import TYPE_CHECKING, List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.config import Base

if TYPE_CHECKING:
    from app.models.tool import Tool

class Workspace(Base):
    __tablename__ = "workspace"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(index=True)
    # relationships
    tools: Mapped[List["Tool"]] = relationship(back_populates="workspace", cascade="all, delete-orphan")