from fastapi import APIRouter
from sqlmodel import select
from app.api.dependencies import DbSession

from app.models.device import Device
from app.models.device_type import DeviceType, DeviceTypeCreate
from app.models.device_software import DeviceSoftware
from app.models.software import Software, SoftwareCreate, SoftwarePublic
from app.models.experiment import Experiment
from app.models.reserved_experiment import ReservedExperiment
from app.models.schema import Schema
from app.models.server import Server


router = APIRouter()


@router.get("/")
def get_all(db: DbSession): 
    stmt = select(Software)
    return db.exec(stmt).all()


@router.get("/{id}", response_model=SoftwarePublic)
def get_by_id(db: DbSession, id: int): 
    stmt = select(Software).where(Software.id == id)
    return db.exec(stmt).one_or_none()


@router.post("/")
def create(db: DbSession, software: SoftwareCreate):
    db_software = Software.model_validate(software)
    db.add(db_software)
    db.commit()
    db.refresh(db_software)
    return db_software


@router.delete("/{id}")
def delete(db: DbSession, id: int):
    db_software = get_by_id(db, id)
    if not db_software:
        return None
    db.delete(db_software)
    db.commit()
    return db_software