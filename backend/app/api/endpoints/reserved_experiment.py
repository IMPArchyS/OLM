from fastapi import APIRouter
from sqlmodel import select
from app.api.dependencies import DbSession

from app.models.device import Device
from app.models.device_type import DeviceType, DeviceTypeCreate
from app.models.device_software import DeviceSoftware
from app.models.software import Software
from app.models.experiment import Experiment
from app.models.reserved_experiment import ReservedExperiment, ReservedExperimentCreate, ReservedExperimentPublic
from app.models.schema import Schema
from app.models.server import Server


router = APIRouter()


@router.get("/")
def get_all(db: DbSession): 
    stmt = select(ReservedExperiment)
    return db.exec(stmt).all()


@router.get("/{id}", response_model=ReservedExperimentPublic)
def get_by_id(db: DbSession, id: int): 
    stmt = select(ReservedExperiment).where(ReservedExperiment.id == id)
    return db.exec(stmt).one_or_none()


@router.post("/")
def create(db: DbSession, reserved_experiment: ReservedExperimentCreate):
    db_reserved_exp = ReservedExperiment.model_validate(reserved_experiment)
    db.add(db_reserved_exp)
    db.commit()
    db.refresh(db_reserved_exp)
    return db_reserved_exp


@router.delete("/{id}")
def delete(db: DbSession, id: int):
    db_reserved_experiment = get_by_id(db, id)
    if not db_reserved_experiment:
        return None
    db.delete(db_reserved_experiment)
    db.commit()
    return db_reserved_experiment