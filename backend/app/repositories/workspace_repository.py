from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from app.models.workspace import Workspace


class WorkspaceRepository:
    def __init__(self, db_session: Session) -> None:
        self.db_session = db_session

    def get_workspace_by_id(self, workspace_id: int) -> Optional[Workspace]:
        statement = select(Workspace).options(selectinload(Workspace.tools)).where(Workspace.id == workspace_id)
        return self.db_session.execute(statement).scalar_one_or_none()

    def get_all_workspaces(self) -> List[Workspace]:
        statement = select(Workspace)
        return list(self.db_session.execute(statement).scalars().all())

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
