from fastapi import APIRouter, HTTPException, status
from sqlmodel import select
from app.api.dependencies import DbSession

from app.models.device_type import DeviceType, DeviceTypeCreate, DeviceTypePublic, DeviceTypeSync, DeviceTypeUpdate
from app.models.utils import ensure, now


router = APIRouter()


def sync_device_type(db: DbSession, device_type: DeviceTypeSync):
    db_device_type = db.exec(select(DeviceType).where(DeviceType.name == device_type.name)).first()
    
    if not db_device_type:
        db_device_type = create(db, DeviceTypeCreate(name=device_type.name))
    else:
        db_device_type = update(db, ensure(db_device_type.id), DeviceTypeUpdate(name=device_type.name))
    
    return DeviceTypeSync.model_validate(db_device_type, from_attributes=True)


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


@router.post("/", status_code=status.HTTP_201_CREATED)
def create(db: DbSession, device_type: DeviceTypeCreate):
    db_device_type = DeviceType.model_validate(device_type)
    db.add(db_device_type)
    db.commit()
    db.refresh(db_device_type)
    return db_device_type


@router.patch("/{id}", response_model=DeviceTypeUpdate)
def update(db: DbSession, id: int, device_type: DeviceTypeUpdate):
    db_device_type = db.get(DeviceType, id)
    if not db_device_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Device Type with {id} not found!")
    device_type_data = device_type.model_dump(exclude_unset=True)
    db_device_type.sqlmodel_update(device_type_data)
    db_device_type.modified_at = now()
    db.add(db_device_type)
    db.commit()
    db.refresh(db_device_type)
    return db_device_type
