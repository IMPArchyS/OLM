from fastapi import APIRouter, HTTPException, Response, status
from sqlmodel import select
from app.api.dependencies import DbSession

from app.models.device import Device, DevicePublic
from app.models.device_type import DeviceType
from app.models.device_software import DeviceSoftware
from app.models.software import Software
from app.models.experiment import Experiment
from app.models.reserved_experiment import ReservedExperiment
from app.models.schema import Schema
from app.models.server import Server, ServerCreate, ServerPublic, ServerPubDetailed, ServerUpdate


ServerPubDetailed.model_rebuild()


router = APIRouter()


@router.get("/")
def get_all(db: DbSession): 
    stmt = select(Server)
    return db.exec(stmt).all()


@router.get("/{id}", response_model=ServerPublic)
def get_by_id(db: DbSession, id: int):
    db_server = db.get(Server, id)
    if not db_server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Server with {id} not found!")
    return db_server


@router.post("/", status_code=status.HTTP_201_CREATED)
def create(db: DbSession, server: ServerCreate):
    db_server = Server.model_validate(server)
    db.add(db_server)
    db.commit()
    db.refresh(db_server)
    return db_server


@router.patch("/{id}", response_model=ServerUpdate)
def update(db: DbSession, id: int, server: ServerUpdate):
    db_server = db.get(Server, id)
    if not db_server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Server with {id} not found!")
    server_data = server.model_dump(exclude_unset=True)
    db_server.sqlmodel_update(server_data)
    db.add(db_server)
    db.commit()
    db.refresh(db_server)
    return db_server


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(db: DbSession, id: int):
    db_server = db.get(Server, id)
    if not db_server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Server with {id} not found!")
    db.delete(db_server)
    db.commit()
    return db_server