from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.config import Base

if TYPE_CHECKING:
    from app.models.tool import Tool


class Reservation(Base):
    __tablename__ = "reservation"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    start_time: Mapped[datetime] = mapped_column(DateTime, default=None)
    end_time: Mapped[datetime] = mapped_column(DateTime, default=None)
    # relationships
    user_id: Mapped[Optional[int]] = mapped_column(default=None)
    tool_id: Mapped[int] = mapped_column(ForeignKey("tool.id"))
    tool: Mapped["Tool"] = relationship(back_populates="reservations")