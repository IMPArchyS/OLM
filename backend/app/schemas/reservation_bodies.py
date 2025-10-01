from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ReservationBase(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    user_id: Optional[int] = None
    tool_id: int


class ReservationCreate(ReservationBase):
    pass


class ReservationUpdate(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    user_id: Optional[int] = None
    tool_id: Optional[int] = None


class ToolResponse(BaseModel):
    id: int
    name: str
    occupied: bool
    workspace_id: int
    
    class Config:
        from_attributes = True


class ReservationResponse(ReservationBase):
    id: int
    tool: Optional[ToolResponse] = None
    
    class Config:
        from_attributes = True