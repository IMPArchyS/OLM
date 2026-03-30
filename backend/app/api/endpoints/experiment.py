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
logger = logging.getLogger(__name__)


def _get_reservations_for_device_from(db: DbSession, device_id: int, from_time: datetime) -> list[Reservation]:
    stmt = (
        select(Reservation)
        .where(Reservation.device_id == device_id, Reservation.end > from_time)
        .order_by(col(Reservation.start))
    )
    return list(db.exec(stmt).all())


def _maintenance_window_for_day(
    day: date,
    maintenance_start: time,
    maintenance_end: time,
    tzinfo,
) -> tuple[datetime, datetime]:
    start_dt = datetime.combine(day, maintenance_start, tzinfo=tzinfo)
    end_day = day if maintenance_start <= maintenance_end else day + timedelta(days=1)
    end_dt = datetime.combine(end_day, maintenance_end, tzinfo=tzinfo)
    return start_dt, end_dt


def _first_overlapping_maintenance_window(
    range_start: datetime,
    range_end: datetime,
    maintenance_start: time | None,
    maintenance_end: time | None,
) -> tuple[datetime, datetime] | None:
    if maintenance_start is None or maintenance_end is None:
        return None
    if maintenance_start == maintenance_end:
        return None

    day = range_start.date() - timedelta(days=1)
    last_day = range_end.date()

    while day <= last_day:
        window_start, window_end = _maintenance_window_for_day(
            day,
            maintenance_start,
            maintenance_end,
            range_start.tzinfo,
        )
        if window_start < range_end and window_end > range_start:
            return window_start, window_end
        day += timedelta(days=1)

    return None


def _find_next_non_conflicting_start(
    start_from: datetime,
    simulation_time_seconds: int,
    reservations: list[Reservation],
    maintenance_start: time | None,
    maintenance_end: time | None,
) -> datetime:
    run_window = timedelta(seconds=simulation_time_seconds)
    candidate = start_from

    while True:
        run_end = candidate + run_window

        overlapping_reservation = None
        for reservation in reservations:
            if reservation.end <= candidate:
                continue
            if reservation.start < run_end and reservation.end > candidate:
                overlapping_reservation = reservation
                break

        if overlapping_reservation is not None:
            candidate = max(candidate, overlapping_reservation.end)
            continue

        overlapping_maintenance = _first_overlapping_maintenance_window(
            candidate,
            run_end,
            maintenance_start,
            maintenance_end,
        )
        if overlapping_maintenance is not None:
            _, maintenance_window_end = overlapping_maintenance
            candidate = max(candidate, maintenance_window_end)
            continue

        return candidate


def _is_reserved_now(at_time: datetime, reservations: list[Reservation]) -> bool:
    return any(reservation.start <= at_time < reservation.end for reservation in reservations)


def _plan_dispatch_time(
    db: DbSession,
    device_id: int,
    simulation_time_seconds: int,
    reference_time: datetime,
    maintenance_start: time | None,
    maintenance_end: time | None,
) -> tuple[datetime, bool]:
    reservations = _get_reservations_for_device_from(db, device_id, reference_time)
    dispatch_at = _find_next_non_conflicting_start(
        reference_time,
        simulation_time_seconds,
        reservations,
        maintenance_start,
        maintenance_end,
    )
    return dispatch_at, _is_reserved_now(reference_time, reservations)


async def _forward_queue_and_store_log(
    base_url: str,
    experiment: ExperimentFormQueue,
    device: Device,
    server_id: int,
    attempt: int = 1,
) -> bool:
    try:
        experiment_payload = ExperimentQueue(
            id=experiment.id,
            user_id=experiment.user_id,
            command=experiment.command,
            setpoint_changes=experiment.setpoint_changes,
            input_arguments=experiment.input_arguments,
            output_arguments=experiment.output_arguments,
            simulation_time=experiment.simulation_time,
            sample_rate=experiment.sample_rate,
            software_name=experiment.software_name,
            device_name=device.name,
            schema_id=experiment.schema_id,
        )
        async with httpx.AsyncClient(timeout=None) as client:
            headers = {"X-API-KEY": settings.EXPERIMENTAL_API_KEY}
            response = await client.post(f"{base_url}/api/server/experiment", json=experiment_payload.model_dump(), headers=headers)
        response.raise_for_status()

        body = response.json()
        if not isinstance(body, dict):
            logger.error("Queue callback returned unexpected response type: %s", type(body))
            return True

        # Remote log payload contains server-side metadata (device/software). We only persist
        # what belongs to our domain model: user, local experiment, runs, optional note.
        experiment_log_payload = ExperimentLogCreate.model_validate(
            {
                "user_id": experiment.user_id,
                "experiment_id": experiment.id,
                "device_id": device.id,
                "server_id": server_id,
                "run": body.get("run", body.get("runs")),
                "note": body.get("note"),
                "started_at": body.get("started_at"),
                "stopped_at": body.get("stopped_at"),
                "timedout_at": body.get("timedout_at"),
                "finished_at": body.get("finished_at"),
            }
        )

        with Session(engine) as task_db:
            create_experiment_log(task_db, experiment_log_payload, experiment.user_id)
        return True
    except httpx.HTTPStatusError as e:
        retryable = e.response.status_code >= 500 or e.response.status_code == 429
        logger.error(
            "Queued experiment failed on remote server (attempt %s, status %s, retryable=%s): %s",
            attempt,
            e.response.status_code,
            retryable,
            e.response.text,
        )
        return not retryable
    except httpx.RequestError as e:
        logger.error(
            "Queued experiment request failed to reach remote server (attempt %s): %s",
            attempt,
            str(e),
        )
        return False
    except Exception as e:
        logger.exception(
            "Unexpected error while processing queued experiment (attempt %s): %s",
            attempt,
            str(e),
        )
        return False


async def _dispatch_queue_with_retry(
    base_url: str,
    experiment: ExperimentFormQueue,
    device: Device,
    server_id: int,
    initial_dispatch_at: datetime,
    retry_interval_seconds: int = 60,
):
    dispatch_at = initial_dispatch_at
    attempt = 1

    while True:
        wait_seconds = (dispatch_at - now()).total_seconds()
        if wait_seconds > 0:
            await asyncio.sleep(wait_seconds)

        done = await _forward_queue_and_store_log(
            base_url,
            experiment,
            device,
            server_id,
            attempt=attempt,
        )
        if done:
            return

        logger.warning(
            "Retrying queued experiment %s for device %s in %s seconds",
            experiment.id,
            device.id,
            retry_interval_seconds,
        )
        await asyncio.sleep(retry_interval_seconds)

        with Session(engine) as scheduling_db:
            latest_device = scheduling_db.get(Device, ensure(device.id))
            if latest_device is None:
                logger.error("Cannot retry queued experiment %s: device %s not found", experiment.id, device.id)
                return

            dispatch_at, _ = _plan_dispatch_time(
                scheduling_db,
                device_id=ensure(latest_device.id),
                simulation_time_seconds=experiment.simulation_time,
                reference_time=now(),
                maintenance_start=latest_device.maintenance_start,
                maintenance_end=latest_device.maintenance_end,
            )
        attempt += 1


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
    dispatch_at, is_reserved_now = _plan_dispatch_time(
        db,
        device_id=ensure(db_device.id),
        simulation_time_seconds=experiment.simulation_time,
        reference_time=request_time,
        maintenance_start=db_device.maintenance_start,
        maintenance_end=db_device.maintenance_end,
    )
    scheduled_delay_seconds = max(0, int((dispatch_at - request_time).total_seconds()))

    asyncio.create_task(
        _dispatch_queue_with_retry(
            base_url,
            experiment,
            db_device,
            ensure(db_server.id),
            initial_dispatch_at=dispatch_at,
        )
    )

    detail = f"Experiment queued on server {db_server.id}"
    if scheduled_delay_seconds > 0:
        detail = f"Experiment scheduled on server {db_server.id} at {dispatch_at.isoformat()}"

    return {
        "detail": detail,
        "server_id": db_server.id,
        "experiment_id": experiment.id,
        "scheduled_for": dispatch_at.isoformat(),
        "scheduled_delay_seconds": scheduled_delay_seconds,
        "device_reserved_now": is_reserved_now,
        "queued_immediately": scheduled_delay_seconds == 0,
    }


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