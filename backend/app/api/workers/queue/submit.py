import asyncio
import logging
from dataclasses import dataclass, field
from datetime import timedelta

import httpx
from pydantic import ValidationError
from sqlalchemy import or_
from sqlmodel import Session, col, select

from app.api.dependencies import engine
from app.api.endpoints.server import resolve_url
from app.core.config import settings
from app.models.device import Device
from app.models.experiment import ExperimentQueuePayload
from app.models.experiment_log import ExperimentLog
from app.models.experiment_queue import ExperimentQueue, QueueStatus
from app.models.server import Server
from app.models.utils import now
from .helpers import find_overlapping_reservation, maintenance_overlap_end, mark_retry_or_fail, queue_now

logger = logging.getLogger("uvicorn.error")


@dataclass
class _SubmitContext:
    entry_id: int
    url: str
    payload_json: dict
    any_device_mode: bool = False
    locked_device_id: int | None = None
    locked_server_id: int | None = None


def _fetch_submit_ids() -> list[int]:
    current_time = queue_now()
    with Session(engine) as session:
        stmt = (
            select(ExperimentQueue)
            .where(
                ExperimentQueue.status == QueueStatus.NOT_STARTED,
                or_(
                    col(ExperimentQueue.next_attempt_at).is_(None),
                    col(ExperimentQueue.next_attempt_at) <= current_time,
                ),
            )
            .order_by(col(ExperimentQueue.created_at))
            .limit(settings.EXPERIMENT_QUEUE_BATCH_SIZE)
        )
        return [e.id for e in session.exec(stmt).all() if e.id is not None]


def _prepare_explicit(session: Session, entry: ExperimentQueue) -> _SubmitContext | None:
    entry_id = entry.id

    server = session.get(Server, entry.server_id)
    if server is None or not (server.available and server.enabled and server.production):
        logger.info("WORKER: submit skipped queue_id=%s reason=server_unavailable", entry_id)
        mark_retry_or_fail(entry)
        session.commit()
        return None

    base_url = resolve_url(server)
    if not base_url:
        mark_retry_or_fail(entry)
        session.commit()
        return None

    try:
        raw = entry.payload
        payload = raw if isinstance(raw, ExperimentQueuePayload) else ExperimentQueuePayload.model_validate(raw)
    except ValidationError:
        logger.exception("WORKER: payload validation failed queue_id=%s", entry_id)
        mark_retry_or_fail(entry)
        session.commit()
        return None

    device = session.get(Device, entry.device_id)
    if device is None:
        logger.info("WORKER: submit skipped queue_id=%s reason=device_missing", entry_id)
        mark_retry_or_fail(entry)
        session.commit()
        return None

    run_start = now()
    sim_time = max(0, int(payload.simulation_time))
    run_end = run_start + timedelta(seconds=sim_time)
    logger.info(
        "WORKER: submit try queue_id=%s server=%s device=%s attempts=%s sim_time=%s",
        entry_id, entry.server_id, entry.device_id, entry.attempts, sim_time,
    )

    mo_end = maintenance_overlap_end(device, run_start, run_end)
    if mo_end is not None:
        entry.status = QueueStatus.NOT_STARTED
        entry.next_attempt_at = mo_end.replace(tzinfo=None)
        entry.modified_at = queue_now()
        session.commit()
        logger.info("WORKER: submit deferred queue_id=%s reason=maintenance_overlap", entry_id)
        return None

    overlap = find_overlapping_reservation(session, entry.device_id, run_start, run_end)
    if overlap is not None:
        entry.status = QueueStatus.NOT_STARTED
        entry.next_attempt_at = overlap.end.replace(tzinfo=None)
        entry.modified_at = queue_now()
        session.commit()
        logger.info("WORKER: submit deferred queue_id=%s reason=reservation_overlap", entry_id)
        return None

    return _SubmitContext(
        entry_id=entry_id,
        url=f"{base_url}{settings.EXPERIMENT_QUEUE_SUBMIT_PATH}",
        payload_json=payload.model_dump(mode="json"),
    )


def _prepare_any_device(session: Session, entry: ExperimentQueue) -> _SubmitContext | None:
    entry_id = entry.id

    try:
        raw = entry.payload
        payload = raw if isinstance(raw, ExperimentQueuePayload) else ExperimentQueuePayload.model_validate(raw)
    except ValidationError:
        logger.exception("WORKER: payload validation failed queue_id=%s", entry_id)
        entry.status = QueueStatus.FAILED
        entry.modified_at = queue_now()
        session.commit()
        return None

    candidates = payload.candidate_device_ids or []
    if not candidates:
        logger.info("WORKER: submit failed queue_id=%s reason=no_candidates", entry_id)
        entry.status = QueueStatus.FAILED
        entry.modified_at = queue_now()
        session.commit()
        return None

    run_start = now()
    sim_time = max(0, int(payload.simulation_time))
    run_end = run_start + timedelta(seconds=sim_time)

    for device_id in candidates:
        device = session.get(Device, device_id)
        if device is None or device.deleted_at is not None:
            continue

        server = session.get(Server, device.server_id)
        if server is None or not (server.available and server.enabled and server.production):
            continue

        base_url = resolve_url(server)
        if not base_url:
            continue

        if maintenance_overlap_end(device, run_start, run_end) is not None:
            continue

        if find_overlapping_reservation(session, device_id, run_start, run_end) is not None:
            continue

        submit_payload = payload.model_copy(update={"device_name": device.name})
        logger.info(
            "WORKER: submit try (any-device) queue_id=%s device=%s server=%s sim_time=%s",
            entry_id, device_id, device.server_id, sim_time,
        )
        return _SubmitContext(
            entry_id=entry_id,
            url=f"{base_url}{settings.EXPERIMENT_QUEUE_SUBMIT_PATH}",
            payload_json=submit_payload.model_dump(mode="json"),
            any_device_mode=True,
            locked_device_id=device_id,
            locked_server_id=device.server_id,
        )

    entry.status = QueueStatus.NOT_STARTED
    entry.next_attempt_at = queue_now() + timedelta(seconds=settings.EXPERIMENT_QUEUE_RETRY_BASE_SECONDS)
    entry.modified_at = queue_now()
    session.commit()
    logger.info("WORKER: submit deferred queue_id=%s reason=no_device_available", entry_id)
    return None


def _prepare(entry_id: int) -> _SubmitContext | None:
    with Session(engine) as session:
        entry = session.get(ExperimentQueue, entry_id)
        if entry is None:
            return None
        if entry.device_id is None:
            return _prepare_any_device(session, entry)
        return _prepare_explicit(session, entry)


def _on_retry(entry_id: int) -> None:
    with Session(engine) as session:
        entry = session.get(ExperimentQueue, entry_id)
        if entry is None:
            return
        mark_retry_or_fail(entry)
        session.commit()
        logger.info(
            "WORKER: retry queue_id=%s attempts=%s status=%s",
            entry_id, entry.attempts, entry.status,
        )


def _on_defer(entry_id: int) -> None:
    with Session(engine) as session:
        entry = session.get(ExperimentQueue, entry_id)
        if entry:
            entry.status = QueueStatus.NOT_STARTED
            entry.next_attempt_at = queue_now() + timedelta(seconds=settings.EXPERIMENT_QUEUE_RETRY_BASE_SECONDS)
            entry.modified_at = queue_now()
            session.commit()
    logger.info("WORKER: deferred queue_id=%s reason=any_device_http_failure", entry_id)


def _on_accepted(
    entry_id: int,
    job_id: str,
    locked_device_id: int | None,
    locked_server_id: int | None,
) -> None:
    with Session(engine) as session:
        entry = session.get(ExperimentQueue, entry_id)
        if entry is None:
            return
        entry.job_id = job_id
        entry.status = QueueStatus.PENDING
        entry.next_attempt_at = None
        entry.modified_at = queue_now()

        if locked_device_id is not None:
            entry.device_id = locked_device_id
            entry.server_id = locked_server_id
            exp_log = ExperimentLog(
                user_id=entry.user_id,
                experiment_id=entry.experiment_id,
                device_id=locked_device_id,
                server_id=locked_server_id,
                started_at=now(),
                finished_at=None,
                run=None,
            )
            session.add(exp_log)
            session.flush()
            entry.experiment_log_id = exp_log.id
        else:
            exp_log = session.get(ExperimentLog, entry.experiment_log_id)
            if exp_log is not None and exp_log.started_at is None:
                exp_log.started_at = now()
                exp_log.modified_at = now()

        session.commit()
        logger.info("WORKER: submit accepted queue_id=%s job_id=%s", entry_id, job_id)


async def submit_entry(client: httpx.AsyncClient, entry_id: int) -> None:
    ctx = await asyncio.to_thread(_prepare, entry_id)
    if ctx is None:
        return

    logger.info("WORKER: submit request queue_id=%s url=%s", entry_id, ctx.url)
    try:
        response = await client.post(
            ctx.url,
            json=ctx.payload_json,
            headers={"x-api-key": settings.EXPERIMENTAL_API_KEY},
        )
    except httpx.RequestError:
        logger.info("WORKER: submit request failed queue_id=%s", entry_id)
        if ctx.any_device_mode:
            await asyncio.to_thread(_on_defer, entry_id)
        else:
            await asyncio.to_thread(_on_retry, entry_id)
        return

    logger.info("WORKER: submit response queue_id=%s status_code=%s", entry_id, response.status_code)

    if response.status_code == 202:
        try:
            job_id = response.json().get("job_id")
        except ValueError:
            job_id = None
        if job_id:
            await asyncio.to_thread(
                _on_accepted, entry_id, str(job_id),
                ctx.locked_device_id, ctx.locked_server_id,
            )
            return

    if ctx.any_device_mode:
        await asyncio.to_thread(_on_defer, entry_id)
    else:
        await asyncio.to_thread(_on_retry, entry_id)


async def run_submit_tick(client: httpx.AsyncClient) -> None:
    entry_ids = await asyncio.to_thread(_fetch_submit_ids)
    if not entry_ids:
        return
    logger.info("WORKER: submit tick count=%s", len(entry_ids))
    for entry_id in entry_ids:
        await submit_entry(client, entry_id)
