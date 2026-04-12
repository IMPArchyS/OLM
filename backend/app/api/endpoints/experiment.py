from typing import List
from fastapi import APIRouter, HTTPException, status
import asyncio
import logging
import httpx
from datetime import datetime, timedelta, time, date
from sqlmodel import Session, col, select
from app.api.dependencies import DbSession, engine
from app.api.endpoints.server import resolve_url
from app.api.endpoints.experiment_log import create as create_experiment_log

from app.models.device import Device, DevicePublic
from app.models.experiment import Experiment, ExperimentCreate, ExperimentPublic, ExperimentFormQueue, ExperimentQueue, ExperimentUpdate
from app.models.experiment_device import ExperimentDevice
from app.models.experiment_log import ExperimentLogCreate
from app.models.reservation import Reservation
from app.models.server import Server
from app.core.config import settings
from app.models.utils import ensure, now


router = APIRouter()


@router.get("/", response_model=list[ExperimentPublic])
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
    stmt = (
        select(Experiment)
        .join(ExperimentDevice, col(ExperimentDevice.experiment_id) == Experiment.id)
        .where(ExperimentDevice.device_id == device_id)
        .distinct()
    )
    db_experiments = db.exec(stmt).all()
    return db_experiments


@router.get("/{id}/devices", response_model=list[DevicePublic])
def get_experiment_devices(db: DbSession, id: int):
    db_experiment = db.get(Experiment, id)
    if not db_experiment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Experiment with {id} not found!")
    return db_experiment.devices


@router.post("/", status_code=status.HTTP_201_CREATED)
def create(db: DbSession, experiment: ExperimentCreate):
    requested_device_ids = []
    if experiment.device_ids:
        requested_device_ids.extend(experiment.device_ids)

    deduplicated_device_ids = list(dict.fromkeys(requested_device_ids))
    db_devices = []
    if deduplicated_device_ids:
        db_devices = list(db.exec(select(Device).where(col(Device.id).in_(deduplicated_device_ids))).all())
        if len(db_devices) != len(deduplicated_device_ids):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or more devices not found!")

    experiment_data = experiment.model_dump(exclude={"device_ids"})
    db_experiment = Experiment.model_validate(experiment_data)
    db_experiment.devices = db_devices

    db.add(db_experiment)
    db.commit()
    db.refresh(db_experiment)
    return db_experiment


@router.post("/queue", status_code=status.HTTP_201_CREATED)
async def queue(db: DbSession, experiment: ExperimentFormQueue):
    if experiment.simulation_time < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="simulation_time must be >= 0")

    db_experiment = db.get(Experiment, experiment.id)
    if not db_experiment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Experiment with {experiment.id} not found!")

    db_device = db.get(Device, experiment.device_id)
    if not db_device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Device with {experiment.device_id} not found!")

    if not any(d.id == db_device.id for d in db_experiment.devices):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Device {db_device.id} is not assigned to experiment {db_experiment.id}!"
        )

    db_server = db.get(Server, db_device.server_id)
    if not db_server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Server with {db_device.server_id} not found!")

    if not (db_server.available and db_server.enabled and db_server.production):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Server with {db_server.id} is not available, enabled, and in production!"
        )

    base_url = resolve_url(db_server)
    if not base_url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Server missing domain!")

    request_time = now()



@router.patch("/{id}", response_model=ExperimentPublic)
def update(db: DbSession, id: int, experiment: ExperimentUpdate):
    db_experiment = db.get(Experiment, id)
    if not db_experiment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Experiment with {id} not found!")
    requested_device_ids = None
    if experiment.device_ids is not None:
        requested_device_ids = list(dict.fromkeys(experiment.device_ids))

    if requested_device_ids is not None:
        db_devices = list(db.exec(select(Device).where(col(Device.id).in_(requested_device_ids))).all())
        if len(db_devices) != len(requested_device_ids):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or more devices not found!")
        db_experiment.devices = db_devices

    experiment_data = experiment.model_dump(exclude_unset=True, exclude={"device_ids"})
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