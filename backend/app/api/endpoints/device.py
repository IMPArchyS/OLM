from fastapi import APIRouter, HTTPException, Response, status
from sqlmodel import select
from app.api.dependencies import DbSession

from app.models.device import Device, DeviceCreate, DevicePublic, DeviceUpdate
from app.models.device_type import DeviceType, DeviceTypeCreate
from app.models.device_software import DeviceSoftware
from app.models.software import Software
from app.models.experiment import Experiment
from app.models.reserved_experiment import ReservedExperiment
from app.models.schema import Schema
from app.models.server import Server


router = APIRouter()


@router.get("/")
def get_all(db: DbSession): 
    stmt = select(Device)
    return db.exec(stmt).all()


@router.get("/{id}", response_model=DevicePublic)
def get_by_id(db: DbSession, id: int): 
    db_device = db.get(Device, id)
    if not db_device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Device with {id} not found!")
    return db_device


@router.post("/", status_code=status.HTTP_201_CREATED)
def create(db: DbSession, device: DeviceCreate):
    db_device = Device.model_validate(device)
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device


@router.patch("/{id}", response_model=DevicePublic)
def update(db: DbSession, id: int, device: DeviceUpdate):
    db_device = db.get(Device, id)
    if not db_device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Device with {id} not found!")
    reserved_device_data = device.model_dump(exclude_unset=True)
    db_device.sqlmodel_update(reserved_device_data)
    
    if not db.get(DeviceType, device.device_type_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Device Type with {device.device_type_id} not found!")    
    
    if not db.get(Server, device.server_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Server with {device.server_id} not found!")    
    
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(db: DbSession, id: int):
    db_device = db.get(Device, id)
    if not db_device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Device with {id} not found!")
    db.delete(db_device)
    db.commit()
    return db_device