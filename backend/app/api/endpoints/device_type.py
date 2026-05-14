from fastapi import APIRouter, HTTPException, status
from sqlmodel import select
from app.api.dependencies import CurrentUser, DbSession

from app.models.device_type import DeviceType, DeviceTypePublic, ModelConfig


router = APIRouter()


@router.get("/", response_model=list[DeviceTypePublic])
def get_all(db: DbSession, _: CurrentUser):
    stmt = select(DeviceType)
    return db.exec(stmt).all()


@router.get("/{id}", response_model=DeviceTypePublic)
def get_by_id(db: DbSession, id: int, _: CurrentUser):
    db_device_type = db.get(DeviceType, id)
    if not db_device_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Device Type with {id} not found!")
    return db_device_type


@router.patch("/{id}/visual-config")
def update_visual_config(db: DbSession, id: int, config: ModelConfig, _: CurrentUser):
    db_device_type = db.get(DeviceType, id)
    if not db_device_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Device Type with {id} not found!")
    db_device_type.visual_config = config.model_dump(mode="json")
    db.add(db_device_type)
    db.commit()
    db.refresh(db_device_type)
    return db_device_type