from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.config import get_session
from app.models.workspace import Workspace
from app.repositories.workspace_repository import WorkspaceRepository
from app.services.workspace_service import (
    WorkspaceService,
)
from app.repositories.tool_repository import ToolRepository

router = APIRouter(tags=["Workspaces"], prefix="/workspace")

def get_workspace_repository(session: Session = Depends(get_session)) -> WorkspaceRepository:
    return WorkspaceRepository(session)

def  get_tool_repository(session: Session = Depends(get_session)) -> ToolRepository:
    return ToolRepository(session)

def get_workspace_service(
    workspace_repository: WorkspaceRepository = Depends(get_workspace_repository),
    tool_repository: ToolRepository = Depends(get_tool_repository)
) -> WorkspaceService:
    return WorkspaceService(workspace_repository, tool_repository)

# Route functions with dependency injection
@router.get("/", response_model=List[Workspace])
def get_all_workspaces(
    service: WorkspaceService = Depends(get_workspace_service)
) -> List[Workspace]:
    return service.get_all_workspaces()

@router.get("/{workspace_id}", response_model=Workspace)
def get_workspace_by_id(
    workspace_id: int,
    service: WorkspaceService = Depends(get_workspace_service)
) -> Workspace | None:
    try:
        return service.get_workspace_by_id(workspace_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/", response_model=Workspace, status_code=status.HTTP_201_CREATED)
def create_workspace(
    workspace: Workspace,
    service: WorkspaceService = Depends(get_workspace_service)
) -> Workspace:
    try:
        return service.create_workspace(workspace)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{workspace_id}", response_model=Workspace)
def update_workspace(
    workspace_id: int,
    workspace: Workspace,
    service: WorkspaceService = Depends(get_workspace_service)
) -> Workspace:
    try:
        return service.update_workspace(workspace_id, workspace)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workspace(
    workspace_id: int,
    service: WorkspaceService = Depends(get_workspace_service)
) -> None:
    try:
        service.delete_workspace(workspace_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))