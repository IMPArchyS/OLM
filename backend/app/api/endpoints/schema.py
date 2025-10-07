from fastapi import APIRouter
from sqlmodel import select
from app.api.dependencies import DbSession

from app.models.device import Device
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
    stmt = select(Schema)
    return db.exec(stmt).all()


@router.get("/{id}")
def get_by_id(db: DbSession, id: int): 
    stmt = select(Schema).where(Schema.id == id)
    return db.exec(stmt).one_or_none()

@router.delete("/{id}")
def delete(db: DbSession, id: int):
    db_schema = get_by_id(db, id)
    if not db_schema:
        return None
    db.delete(db_schema)
    db.commit()
    return db_schema