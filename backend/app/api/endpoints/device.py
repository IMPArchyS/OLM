from fastapi import APIRouter, Response, status
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
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    return db_device


@router.post("/")
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
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    reserved_device_data = device.model_dump(exclude_unset=True)
    db_device.sqlmodel_update(reserved_device_data)
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device


@router.delete("/{id}")
def delete(db: DbSession, id: int):
    db_device = db.get(Device, id)
    if not db_device:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    db.delete(db_device)
    db.commit()
    return db_device