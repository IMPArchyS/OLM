from fastapi import APIRouter, HTTPException, status
from sqlmodel import select
from app.api.dependencies import DbSession

from app.models.device import Device
from app.models.argument import Argument
from app.models.option import Option, OptionCreate, OptionPublic, OptionUpdate
from app.models.device_software import DeviceSoftware
from app.models.software import Software
from app.models.experiment import Experiment
from app.models.reserved_experiment import ReservedExperiment
from app.models.schema import Schema
from app.models.server import Server

router = APIRouter()


@router.get("/")
def get_all(db: DbSession): 
    stmt = select(Option)
    return db.exec(stmt).all()


@router.get("/{id}", response_model=OptionPublic)
def get_by_id(db: DbSession, id: int):
    db_option = db.get(Option, id)
    if not db_option:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Option with {id} not found!")
    return db_option


@router.post("/", status_code=status.HTTP_201_CREATED)
def create(db: DbSession, option: OptionCreate):
    db_option = Option.model_validate(option)
    db.add(db_option)
    db.commit()
    db.refresh(db_option)
    return db_option


@router.patch("/{id}", response_model=OptionUpdate)
def update(db: DbSession, id: int, option: OptionUpdate):
    db_option = db.get(Option, id)
    if not db_option:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Option with {id} not found!")
    device_type_data = option.model_dump(exclude_unset=True)
    db_option.sqlmodel_update(device_type_data)
    
    db.add(db_option)
    db.commit()
    db.refresh(db_option)
    return db_option


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(db: DbSession, id: int):
    db_option = db.get(Option, id)
    if not db_option:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Option with {id} not found!")  
    db.delete(db_option)
    db.commit()
    return db_option