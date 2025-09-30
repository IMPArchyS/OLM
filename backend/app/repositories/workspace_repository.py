from typing import List, Optional
from sqlmodel import Session, select
from app.models.workspace import Workspace


class WorkspaceRepository:
    def __init__(self, db_session: Session) -> None:
        self.db_session = db_session

    def get_workspace_by_id(self, workspace_id: int) -> Optional[Workspace]:
        statement = select(Workspace).where(Workspace.id == workspace_id)
        return self.db_session.exec(statement).first()

    def get_all_workspaces(self) -> List[Workspace]:
        statement = select(Workspace)
        return list(self.db_session.exec(statement).all())

    def create_workspace(self, workspace: Workspace) -> Workspace:
        self.db_session.add(workspace)
        self.db_session.commit()
        self.db_session.refresh(workspace)
        return workspace

    def update_workspace(self, workspace: Workspace) -> Workspace:
        self.db_session.merge(workspace)
        self.db_session.commit()
        self.db_session.refresh(workspace)
        return workspace

    def delete_workspace(self, workspace: Workspace) -> None:
        self.db_session.delete(workspace)
        self.db_session.commit()
