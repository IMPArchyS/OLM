from pydantic import BaseModel
from typing import Optional, List


class ToolBase(BaseModel):
    name: str
    occupied: bool = False
    workspace_id: int


class ToolCreate(ToolBase):
    pass


class ToolUpdate(BaseModel):
    name: Optional[str] = None
    occupied: Optional[bool] = None
    workspace_id: Optional[int] = None


class ReservationResponse(BaseModel):
    id: int
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    user_id: Optional[int] = None
    tool_id: int
    
    class Config:
        from_attributes = True


class ToolResponse(ToolBase):
    id: int
    reservations: List[ReservationResponse] = []
    
    class Config:
        from_attributes = True