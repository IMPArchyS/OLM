from fastapi import APIRouter
from sqlmodel import select
from app.api.dependencies import DbSession

from app.models.device import Device
from app.models.device_type import DeviceType
from app.models.device_software import DeviceSoftware
from app.models.software import Software
from app.models.experiment import Experiment, ExperimentCreate, ExperimentPublic
from app.models.reserved_experiment import ReservedExperiment
from app.models.schema import Schema
from app.models.server import Server, ServerCreate


router = APIRouter()


@router.get("/")
def get_all(db: DbSession): 
    stmt = select(Experiment)
    return db.exec(stmt).all()


@router.get("/{id}", response_model=ExperimentPublic)
def get_by_id(db: DbSession, id: int):
    stmt = select(Experiment).where(Experiment.id == id)
    return db.exec(stmt).one_or_none()


@router.post("/")
def create(db: DbSession, experiment: ExperimentCreate):
    db_experiment = Experiment.model_validate(experiment)
    db.add(db_experiment)
    db.commit()
    db.refresh(db_experiment)
    return db_experiment


@router.delete("/{id}")
def delete(db: DbSession, id: int):
    db_experiment = get_by_id(db, id)
    if not db_experiment:
        return None
    db.delete(db_experiment)
    db.commit()
    return db_experiment