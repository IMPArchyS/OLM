from fastapi import APIRouter, HTTPException, Response, status
from sqlmodel import select
from app.api.dependencies import DbSession

from app.models.device import Device
from app.models.device_type import DeviceType, DeviceTypeCreate
from app.models.device_software import DeviceSoftware
from app.models.software import Software
from app.models.experiment import Experiment
from app.models.reserved_experiment import ReservedExperiment, ReservedExperimentCreate, ReservedExperimentPublic, ReservedExperimentUpdate
from app.models.schema import Schema
from app.models.server import Server


router = APIRouter()


@router.get("/")
def get_all(db: DbSession): 
    stmt = select(ReservedExperiment)
    return db.exec(stmt).all()


@router.get("/{id}", response_model=ReservedExperimentPublic)
def get_by_id(db: DbSession, id: int): 
    db_reserved_exp = db.get(ReservedExperiment, id)
    if not db_reserved_exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reserved Experiment with {id} not found!")
    return db_reserved_exp


@router.post("/", status_code=status.HTTP_201_CREATED)
def create(db: DbSession, reserved_experiment: ReservedExperimentCreate):
    db_reserved_exp = ReservedExperiment.model_validate(reserved_experiment)
    db.add(db_reserved_exp)
    db.commit()
    db.refresh(db_reserved_exp)
    return db_reserved_exp


@router.patch("/{id}", response_model=ReservedExperimentUpdate)
def update(db: DbSession, id: int, reserved_experiment: ReservedExperimentUpdate):
    db_reserved_exp = db.get(ReservedExperiment, id)
    if not db_reserved_exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reserved Experiment with {id} not found!")
    reserved_exp_data = reserved_experiment.model_dump(exclude_unset=True)
    db_reserved_exp.sqlmodel_update(reserved_exp_data)
    db.add(db_reserved_exp)
    db.commit()
    db.refresh(db_reserved_exp)
    return db_reserved_exp


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(db: DbSession, id: int):
    db_reserved_exp = db.get(ReservedExperiment, id)
    if not db_reserved_exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reserved Experiment with {id} not found!")
    db.delete(db_reserved_exp)
    db.commit()
    return db_reserved_exp