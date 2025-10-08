from fastapi import APIRouter, Response, status
from sqlmodel import select
from app.api.dependencies import DbSession

from app.models.device import Device
from app.models.device_type import DeviceType, DeviceTypeCreate, DeviceTypePublic, DeviceTypeUpdate
from app.models.device_software import DeviceSoftware
from app.models.software import Software
from app.models.experiment import Experiment
from app.models.reserved_experiment import ReservedExperiment
from app.models.schema import Schema
from app.models.server import Server


router = APIRouter()


@router.get("/")
def get_all(db: DbSession): 
    stmt = select(DeviceType)
    return db.exec(stmt).all()


@router.get("/{id}", response_model=DeviceTypePublic)
def get_by_id(db: DbSession, id: int):
    db_device_type = db.get(ReservedExperiment, id)
    if not db_device_type:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    return db_device_type


@router.post("/")
def create(db: DbSession, device_type: DeviceTypeCreate):
    db_device_type = DeviceType.model_validate(device_type)
    db.add(db_device_type)
    db.commit()
    db.refresh(db_device_type)
    return db_device_type


@router.patch("/{id}", response_model=DeviceTypeUpdate)
def update(db: DbSession, id: int, device_type: DeviceTypeUpdate):
    db_device_type = db.get(ReservedExperiment, id)
    if not db_device_type:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    device_type_data = device_type.model_dump(exclude_unset=True)
    db_device_type.sqlmodel_update(device_type_data)
    db.add(db_device_type)
    db.commit()
    db.refresh(db_device_type)
    return db_device_type


@router.delete("/{id}")
def delete(db: DbSession, id: int):
    db_device_type = db.get(ReservedExperiment, id)
    if not db_device_type:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    db.delete(db_device_type)
    db.commit()
    return db_device_type