from fastapi import APIRouter
from sqlmodel import select
from app.api.dependencies import DbSession

from app.models.device import Device, DeviceCreate, DevicePublic
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
    stmt = select(Device).where(Device.id == id)
    return db.exec(stmt).one_or_none()


@router.post("/")
def create(db: DbSession, device: DeviceCreate):
    db_device = Device.model_validate(device)
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device


@router.delete("/{id}")
def delete(db: DbSession, id: int):
    db_device = get_by_id(db, id)
    if not db_device:
        return None
    db.delete(db_device)
    db.commit()
    return db_device