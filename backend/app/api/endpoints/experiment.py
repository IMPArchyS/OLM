from typing import List
from fastapi import APIRouter, HTTPException, Response, status
import asyncio
import logging
import httpx
from sqlmodel import Session, select
from app.api.dependencies import DbSession, engine
from app.api.endpoints.server import resolve_url
from app.api.endpoints.experiment_log import create as create_experiment_log

from app.models.device import Device, DevicePublic
from app.models.device_type import DeviceType
from app.models.device_software import DeviceSoftware
from app.models.software import Software
from app.models.experiment import Experiment, ExperimentCreate, ExperimentPublic, ExperimentQueue, ExperimentUpdate
from app.models.experiment_log import ExperimentLog
from app.models.experiment_log import ExperimentLogCreate
from app.models.schema import Schema
from app.models.server import Server, ServerCreate


router = APIRouter()
logger = logging.getLogger(__name__)


async def _forward_queue_and_store_log(base_url: str, experiment: ExperimentQueue):
    try:
        async with httpx.AsyncClient(timeout=None) as client:
            response = await client.post(f"{base_url}/api/server/experiment", json=experiment.model_dump())
        response.raise_for_status()

        body = response.json()
        if not isinstance(body, dict):
            logger.error("Queue callback returned unexpected response type: %s", type(body))
            return

        # Remote log payload contains server-side metadata (device/software). We only persist
        # what belongs to our domain model: user, local experiment, runs, optional note.
        experiment_log_payload = ExperimentLogCreate.model_validate(
            {
                "user_id": experiment.user_id,
                "experiment_id": experiment.id,
                "runs": body.get("runs"),
                "note": body.get("note"),
            }
        )

        with Session(engine) as task_db:
            create_experiment_log(task_db, experiment_log_payload, experiment.user_id)
    except httpx.HTTPStatusError as e:
        logger.error(
            "Queued experiment failed on remote server with status %s: %s",
            e.response.status_code,
            e.response.text,
        )
    except httpx.RequestError as e:
        logger.error("Queued experiment request failed to reach remote server: %s", str(e))
    except Exception as e:
        logger.exception("Unexpected error while processing queued experiment: %s", str(e))


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


@router.post("/queue", status_code=status.HTTP_201_CREATED)
async def queue(db: DbSession, experiment: ExperimentQueue):
    db_experiment = db.get(Experiment, experiment.id)
    if not db_experiment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Experiment with {experiment.id} not found!")

    db_server = db.get(Server, db_experiment.server_id)
    if not db_server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Server with {db_experiment.server_id} not found!")

    if not (db_server.available and db_server.enabled and db_server.production):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Server with {db_server.id} is not available, enabled, and in production!"
        )

    base_url = resolve_url(db_server)
    if not base_url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Server missing domain!")

    # Do not block this API request while remote simulation runs.
    asyncio.create_task(_forward_queue_and_store_log(base_url, experiment))

    return {
        "detail": f"Experiment queued on server {db_server.id}",
        "server_id": db_server.id,
        "experiment_id": experiment.id,
    }


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