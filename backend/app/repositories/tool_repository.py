from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.tool import Tool


class ToolRepository:
    def __init__(self, db_session: Session) -> None:
        self.db_session = db_session

    def get_tool_by_id(self, tool_id: int) -> Optional[Tool]:
        statement = select(Tool).where(Tool.id == tool_id)
        return self.db_session.execute(statement).scalar_one_or_none()

    def get_all_tools(self) -> List[Tool]:
        statement = select(Tool)
        return list(self.db_session.execute(statement).scalars().all())

    def create_tool(self, tool: Tool) -> Tool:
        self.db_session.add(tool)
        self.db_session.commit()
        self.db_session.refresh(tool)
        return tool

    def update_tool(self, tool: Tool) -> Tool:
        self.db_session.merge(tool)
        self.db_session.commit()
        self.db_session.refresh(tool)
        return tool

    def delete_tool(self, tool: Tool) -> None:
        self.db_session.delete(tool)
        self.db_session.commit()