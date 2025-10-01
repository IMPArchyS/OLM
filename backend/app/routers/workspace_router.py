from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.core.config import get_session
from app.schemas.workspace_bodies import WorkspaceCreate, WorkspaceUpdate, WorkspaceResponse
from app.models.workspace import Workspace
from app.repositories.workspace_repository import WorkspaceRepository
from app.services.workspace_service import WorkspaceService
from app.repositories.tool_repository import ToolRepository


router = APIRouter(tags=["Workspaces"], prefix="/workspace")


def get_ws_repo(session: Session = Depends(get_session)) -> WorkspaceRepository:
    return WorkspaceRepository(session)


def  get_tool_repo(session: Session = Depends(get_session)) -> ToolRepository:
    return ToolRepository(session)


def get_ws_service(ws_repo: WorkspaceRepository = Depends(get_ws_repo), tool_repo: ToolRepository = Depends(get_tool_repo)) -> WorkspaceService:
    return WorkspaceService(ws_repo, tool_repo)


WsService = Annotated[WorkspaceService, Depends(get_ws_service)]


@router.get("/", response_model=List[WorkspaceResponse])
def get_all_workspaces(service: WsService) -> List[Workspace]:
    return service.get_all_workspaces()


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace_by_id(workspace_id: int, service: WsService) -> Workspace:
    ws = service.get_workspace_by_id(workspace_id)
    if ws is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workspace with id {workspace_id} not found")
    return ws

@router.post("/", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
def create_workspace(workspace: WorkspaceCreate, service: WsService) -> Workspace:
    try:
        return service.create_workspace(workspace)
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ex))


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
def update_workspace(workspace_id: int, workspace: WorkspaceUpdate, service: WsService) -> Workspace:
    try:
        return service.update_workspace(workspace_id, workspace)
    except ValueError as ex:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ex))


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workspace(workspace_id: int, service: WsService) -> None:
    try:
        service.delete_workspace(workspace_id)
    except ValueError as ex:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ex))