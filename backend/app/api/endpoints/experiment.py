from typing import List
from fastapi import APIRouter, HTTPException, Response, status
from sqlmodel import select
from app.api.dependencies import DbSession

from app.models.device import Device, DevicePublic
from app.models.device_type import DeviceType
from app.models.device_software import DeviceSoftware
from app.models.software import Software
from app.models.experiment import Experiment, ExperimentCreate, ExperimentPublic, ExperimentUpdate
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
    db_experiment = db.get(Experiment, id)
    if not db_experiment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Experiment with {id} not found!")
    return db_experiment


@router.get("/device/{device_id}", response_model=List[ExperimentPublic])
def get_by_device_id(db: DbSession, device_id: int):
    stmt = select(Experiment).where(Experiment.device_id == device_id)
    db_experiments = db.exec(stmt).all()
    return db_experiments


@router.get("/{id}/device", response_model=DevicePublic)
def get_experiment_device(db: DbSession, id: int):
    db_experiment = db.get(Experiment, id)
    if not db_experiment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Experiment with {id} not found!")
    if not db_experiment.device_id:
        return None
    return db_experiment.device

@router.post("/", status_code=status.HTTP_201_CREATED)
def create(db: DbSession, experiment: ExperimentCreate):
    db_experiment = Experiment.model_validate(experiment)
    db.add(db_experiment)
    db.commit()
    db.refresh(db_experiment)
    return db_experiment


@router.patch("/{id}", response_model=ExperimentPublic)
def update(db: DbSession, id: int, experiment: ExperimentUpdate):
    db_experiment = db.get(Experiment, id)
    if not db_experiment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Experiment with {id} not found!")
    experiment_data = experiment.model_dump(exclude_unset=True)
    db_experiment.sqlmodel_update(experiment_data)
    db.add(db_experiment)
    db.commit()
    db.refresh(db_experiment)
    return db_experiment


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(db: DbSession, id: int):
    db_experiment = db.get(Experiment, id)
    if not db_experiment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Experiment with {id} not found!")
    db.delete(db_experiment)
    db.commit()
    return db_experiment