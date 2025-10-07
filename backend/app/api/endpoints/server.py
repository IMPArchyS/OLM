from fastapi import APIRouter
from sqlmodel import select
from app.api.dependencies import DbSession

from app.models.device import Device, DevicePublic
from app.models.device_type import DeviceType
from app.models.device_software import DeviceSoftware
from app.models.software import Software
from app.models.experiment import Experiment
from app.models.reserved_experiment import ReservedExperiment
from app.models.schema import Schema
from app.models.server import Server, ServerCreate, ServerPublic, ServerPubDetailed


ServerPubDetailed.model_rebuild()


router = APIRouter()


@router.get("/")
def get_all(db: DbSession): 
    stmt = select(Server)
    return db.exec(stmt).all()


@router.get("/{id}", response_model=ServerPublic)
def get_by_id(db: DbSession, id: int):
    stmt = select(Server).where(Server.id == id)
    return db.exec(stmt).one_or_none()


@router.post("/")
def create(db: DbSession, server: ServerCreate):
    db_server = Server.model_validate(server)
    db.add(db_server)
    db.commit()
    db.refresh(db_server)
    return db_server


@router.delete("/{id}")
def delete(db: DbSession, id: int):
    db_server = get_by_id(db, id)
    if not db_server:
        return None
    db.delete(db_server)
    db.commit()
    return db_server