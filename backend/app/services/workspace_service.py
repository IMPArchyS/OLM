from typing import Optional
from app.repositories.workspace_repository import WorkspaceRepository
from app.repositories.tool_repository import ToolRepository
from app.models.workspace import Workspace
from app.schemas.workspace_bodies import WorkspaceCreate, WorkspaceUpdate


class WorkspaceService:
    def __init__(self, workspace_repository: WorkspaceRepository, tool_repository: ToolRepository) -> None:
        self.workspace_repository = workspace_repository
        self.tool_repository = tool_repository

    def get_workspace_by_id(self, workspace_id: int) -> Optional[Workspace]:
        return self.workspace_repository.get_workspace_by_id(workspace_id)

    def get_all_workspaces(self) -> list[Workspace]:
        return self.workspace_repository.get_all_workspaces()

    def create_workspace(self, workspace_data: WorkspaceCreate) -> Workspace:
        workspace = Workspace(name=workspace_data.name)
        return self.workspace_repository.create_workspace(workspace)

    def update_workspace(self, workspace_id: int, workspace_data: WorkspaceUpdate) -> Workspace:
        workspace = self.workspace_repository.get_workspace_by_id(workspace_id)
        if not workspace:
            raise ValueError(f"Workspace with id {workspace_id} not found")
        
        workspace.name = workspace_data.name if workspace_data.name is not None else workspace.name
        return self.workspace_repository.update_workspace(workspace)

    def delete_workspace(self, workspace_id: int) -> None:
        workspace = self.workspace_repository.get_workspace_by_id(workspace_id)
        if not workspace:
            raise ValueError(f"Workspace with id {workspace_id} not found")
        self.workspace_repository.delete_workspace(workspace)
