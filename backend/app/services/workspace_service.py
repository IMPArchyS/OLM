from typing import Optional
from app.repositories.workspace_repository import WorkspaceRepository
from app.repositories.tool_repository import ToolRepository
from app.models.workspace import Workspace


class WorkspaceService:
    def __init__(self, workspace_repository: WorkspaceRepository, tool_repository: ToolRepository) -> None:
        self.workspace_repository = workspace_repository
        self.tool_repository = tool_repository

    def create_workspace(self, workspace: Workspace) -> Workspace:
        return self.workspace_repository.create_workspace(workspace)

    def update_workspace(self, workspace_id: int, workspace: Workspace) -> Workspace:
        existing_workspace = self.workspace_repository.get_workspace_by_id(workspace_id)
        if existing_workspace:
            workspace.id = existing_workspace.id
        return self.workspace_repository.update_workspace(workspace)

    def delete_workspace(self, workspace_id: int) -> bool:
        workspace = self.workspace_repository.get_workspace_by_id(workspace_id)
        if workspace:
            self.workspace_repository.delete_workspace(workspace)
            return True
        return False

    def get_workspace_by_id(self, workspace_id: int) -> Optional[Workspace]:
        return self.workspace_repository.get_workspace_by_id(workspace_id)

    def get_all_workspaces(self) -> list[Workspace]:
        return self.workspace_repository.get_all_workspaces()
