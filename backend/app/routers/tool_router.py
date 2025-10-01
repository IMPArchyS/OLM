from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_session
from app.models.tool import Tool
from app.schemas.tool_bodies import ToolCreate, ToolUpdate, ToolResponse
from app.repositories.tool_repository import ToolRepository
from app.services.tool_service import ToolService


router = APIRouter(tags=["Tools"], prefix="/tool")


def get_tool_repo(session: Session = Depends(get_session)) -> ToolRepository:
    return ToolRepository(session)


def get_tool_service(tool_repo: ToolRepository = Depends(get_tool_repo)) -> ToolService:
    return ToolService(tool_repo)


TlService = Annotated[ToolService, Depends(get_tool_service)]


@router.get("/", response_model=List[ToolResponse])
def get_all_tools(service: TlService) -> List[Tool]:
    return service.get_all_tools() 


@router.get("/{tool_id}", response_model=ToolResponse)
def get_tool_by_id(tool_id: int, service: TlService) -> Tool:
    tool = service.get_tool_by_id(tool_id)
    if tool is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tool with id {tool_id} not found")
    return tool


@router.post("/", response_model=ToolResponse, status_code=status.HTTP_201_CREATED)
def create_tool(tool_data: ToolCreate, service: TlService) -> Tool:
    try:
        return service.create_tool(tool_data)
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ex))


@router.patch("/{tool_id}", response_model=ToolResponse)
def update_tool(tool_id: int, tool_data: ToolUpdate, service: TlService) -> Tool:
    try:
        return service.update_tool(tool_id, tool_data)
    except ValueError as ex:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ex))


@router.delete("/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tool(tool_id: int, service: TlService) -> None:
    try:
        service.delete_tool(tool_id)
    except ValueError as ex:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ex))