from fastapi import APIRouter, HTTPException, status
from sqlmodel import select
from app.api.dependencies import DbSession

from app.models.device import Device
from app.models.device_type import DeviceType, DeviceTypeCreate
from app.models.device_software import DeviceSoftware
from app.models.software import Software, SoftwareCreate, SoftwarePublic, SoftwareUpdate
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
    db_software = db.get(Software, id)
    if not db_software:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return db_software


@router.post("/", status_code=status.HTTP_201_CREATED)
def create(db: DbSession, software: SoftwareCreate):
    db_software = Software.model_validate(software)
    db.add(db_software)
    db.commit()
    db.refresh(db_software)
    return db_software


@router.patch("/{id}", response_model=SoftwareUpdate)
def update(db: DbSession, id: int, software: SoftwareUpdate):
    db_software = db.get(Software, id)
    if not db_software:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    software_data = software.model_dump(exclude_unset=True)
    db_software.sqlmodel_update(software_data)
    db.add(db_software)
    db.commit()
    db.refresh(db_software)
    return db_software


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(db: DbSession, id: int):
    db_software = db.get(Software, id)
    if not db_software:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    db.delete(db_software)
    db.commit()
    return db_software