from fastapi import APIRouter, HTTPException, status
from sqlmodel import select
from app.api.dependencies import DbSession

from app.models.device_type import DeviceType, DeviceTypePublic


router = APIRouter()


@router.get("/", response_model=list[DeviceTypePublic])
def get_all(db: DbSession): 
    stmt = select(DeviceType)
    return db.exec(stmt).all()


@router.get("/{id}", response_model=DeviceTypePublic)
def get_by_id(db: DbSession, id: int):
    db_device_type = db.get(DeviceType, id)
    if not db_device_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Device Type with {id} not found!")
    return db_device_type
