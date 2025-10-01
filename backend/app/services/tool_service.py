from typing import List, Optional
from app.repositories.tool_repository import ToolRepository
from app.models.tool import Tool
from app.schemas.tool_bodies import ToolCreate, ToolUpdate


class ToolService:
    def __init__(self, tool_repository: ToolRepository) -> None:
        self.tool_repository = tool_repository

    def get_tool_by_id(self, tool_id: int) -> Optional[Tool]:
        return self.tool_repository.get_tool_by_id(tool_id)

    def get_all_tools(self) -> List[Tool]:
        return self.tool_repository.get_all_tools()

    def create_tool(self, tool_data: ToolCreate) -> Tool:
        tool = Tool(name=tool_data.name, occupied=tool_data.occupied, workspace_id=tool_data.workspace_id)
        return self.tool_repository.create_tool(tool)

    def update_tool(self, tool_id: int, tool_data: ToolUpdate) -> Tool:
        tool = self.tool_repository.get_tool_by_id(tool_id)
        if not tool:
            raise ValueError(f"Tool with id {tool_id} not found")
        tool.name = tool_data.name if tool_data.name is not None else tool.name
        tool.occupied = tool_data.occupied if tool_data.occupied is not None else tool.occupied
        tool.workspace_id = tool_data.workspace_id if tool_data.workspace_id is not None else tool.workspace_id
        return self.tool_repository.update_tool(tool)

    def delete_tool(self, tool_id: int) -> None:
        tool = self.tool_repository.get_tool_by_id(tool_id)
        if not tool:
            raise ValueError(f"Tool with id {tool_id} not found")
        return self.tool_repository.delete_tool(tool)