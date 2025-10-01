from pydantic import BaseModel
from typing import Optional, List


class WorkspaceBase(BaseModel):
    name: str


class WorkspaceCreate(WorkspaceBase):
    pass


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None


class ToolResponse(BaseModel):
    id: int
    name: str
    occupied: bool
    workspace_id: int
    
    class Config:
        from_attributes = True


class WorkspaceResponse(WorkspaceBase):
    id: int
    tools: List[ToolResponse] = []
    
    class Config:
        from_attributes = True