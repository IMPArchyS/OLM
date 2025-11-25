from fastapi import APIRouter, HTTPException, status
from sqlmodel import select
from app.api.dependencies import DbSession

from app.models.device import Device
from app.models.argument import Argument, ArgumentPublic, ArgumentCreate, ArgumentUpdate
from app.models.device_software import DeviceSoftware
from app.models.software import Software
from app.models.experiment import Experiment
from app.models.reserved_experiment import ReservedExperiment
from app.models.schema import Schema
from app.models.server import Server

router = APIRouter()


@router.get("/")
def get_all(db: DbSession): 
    stmt = select(Argument)
    return db.exec(stmt).all()


@router.get("/{id}", response_model=ArgumentPublic)
def get_by_id(db: DbSession, id: int):
    db_argument = db.get(Argument, id)
    if not db_argument:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Argument with {id} not found!")
    return db_argument


@router.post("/", status_code=status.HTTP_201_CREATED)
def create(db: DbSession, argument: ArgumentCreate):
    db_argument = Argument.model_validate(argument)
    db.add(db_argument)
    db.commit()
    db.refresh(db_argument)
    return db_argument


@router.patch("/{id}", response_model=ArgumentUpdate)
def update(db: DbSession, id: int, argument: ArgumentUpdate):
    db_argument = db.get(Argument, id)
    if not db_argument:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Argument with {id} not found!")
    device_type_data = argument.model_dump(exclude_unset=True)
    db_argument.sqlmodel_update(device_type_data)
    
    db.add(db_argument)
    db.commit()
    db.refresh(db_argument)
    return db_argument


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(db: DbSession, id: int):
    db_argument = db.get(Argument, id)
    if not db_argument:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Argument with {id} not found!")  
    db.delete(db_argument)
    db.commit()
    return db_argument