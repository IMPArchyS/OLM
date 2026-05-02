import asyncio
import logging
from dataclasses import dataclass

import httpx
from sqlmodel import Session, col, select

from app.api.dependencies import engine
from app.api.endpoints.server import resolve_url
from app.core.config import settings
from app.models.experiment_log import ExperimentLog, FinishReason
from app.models.experiment_queue import ExperimentQueue, QueueStatus
from app.models.server import Server
from app.models.utils import now
from .helpers import normalize_finish_reason, parse_datetime, queue_now

logger = logging.getLogger("uvicorn.error")

_poll_counts: dict[int, int] = {}


@dataclass
class _PollContext:
    entry_id: int
    job_id: str
    url: str
    experiment_log_id: int


def _fetch_pending_ids() -> list[int]:
    with Session(engine) as session:
        stmt = (
            select(ExperimentQueue)
            .where(ExperimentQueue.status == QueueStatus.PENDING)
            .order_by(col(ExperimentQueue.created_at))
            .limit(settings.EXPERIMENT_QUEUE_BATCH_SIZE)
        )
        return [e.id for e in session.exec(stmt).all() if e.id is not None]


def _prepare_poll(entry_id: int) -> _PollContext | None:
    with Session(engine) as session:
        entry = session.get(ExperimentQueue, entry_id)
        if entry is None or not entry.job_id:
            return None

        server = session.get(Server, entry.server_id)
        if server is None or not (server.available and server.enabled and server.production):
            logger.info("QUEUE: poll deferred queue_id=%s reason=server_unavailable", entry_id)
            return None

        base_url = resolve_url(server)
        if not base_url:
            return None

        status_path = settings.EXPERIMENT_QUEUE_STATUS_PATH.format(job_id=entry.job_id)
        return _PollContext(
            entry_id=entry_id,
            job_id=entry.job_id,
            url=f"{base_url}{status_path}",
            experiment_log_id=entry.experiment_log_id,
        )


def _mark_poll_failed(entry_id: int) -> None:
    with Session(engine) as session:
        entry = session.get(ExperimentQueue, entry_id)
        if entry:
            entry.status = QueueStatus.FAILED
            entry.next_attempt_at = None
            entry.modified_at = queue_now()
            session.commit()
    logger.info("QUEUE: poll failed queue_id=%s reason=max_poll_attempts", entry_id)


def _finalize_resolved(entry_id: int, job_id: str, payload: dict) -> None:
    remote_runs = payload.get("run") or payload.get("runs")
    remote_started_at = parse_datetime(payload.get("started_at"))
    remote_finished_at = parse_datetime(payload.get("finished_at"))
    remote_finish_reason = normalize_finish_reason(payload.get("finish_reason"))

    with Session(engine) as session:
        entry = session.get(ExperimentQueue, entry_id)
        if entry is None:
            return

        exp_log = session.get(ExperimentLog, entry.experiment_log_id)
        if exp_log is not None:
            if exp_log.started_at is None:
                exp_log.started_at = remote_started_at or now()
                exp_log.modified_at = now()
            if remote_finished_at is not None:
                exp_log.finished_at = remote_finished_at
            exp_log.finish_reason = remote_finish_reason
            exp_log.run = remote_runs
            exp_log.modified_at = now()

        entry.status = (
            QueueStatus.FAILED
            if remote_finish_reason in {FinishReason.EXCEPTION_ERROR, FinishReason.DEVICE_TIMEOUT}
            else QueueStatus.FINISHED
        )
        entry.next_attempt_at = None
        entry.modified_at = queue_now()
        final_status = entry.status
        session.commit()

    logger.info(
        "QUEUE: poll resolved queue_id=%s job_id=%s status=%s finish_reason=%s",
        entry_id, job_id, final_status, remote_finish_reason,
    )


async def poll_entry(client: httpx.AsyncClient, entry_id: int) -> None:
    count = _poll_counts.get(entry_id, 0)

    if count >= settings.EXPERIMENT_QUEUE_MAX_POLL_ATTEMPTS:
        await asyncio.to_thread(_mark_poll_failed, entry_id)
        _poll_counts.pop(entry_id, None)
        return

    ctx = await asyncio.to_thread(_prepare_poll, entry_id)
    if ctx is None:
        return

    logger.info("QUEUE: poll try queue_id=%s job_id=%s attempt=%s", entry_id, ctx.job_id, count + 1)
    try:
        response = await client.get(ctx.url, headers={"x-api-key": settings.EXPERIMENTAL_API_KEY})
    except httpx.RequestError:
        logger.info("QUEUE: poll request failed queue_id=%s job_id=%s", entry_id, ctx.job_id)
        _poll_counts[entry_id] = count + 1
        return

    logger.info(
        "QUEUE: poll response queue_id=%s job_id=%s status_code=%s",
        entry_id, ctx.job_id, response.status_code,
    )

    if response.status_code != 200:
        _poll_counts[entry_id] = count + 1
        return

    try:
        payload = response.json()
    except ValueError:
        _poll_counts[entry_id] = count + 1
        return

    remote_runs = payload.get("run") or payload.get("runs")
    remote_finished_at = parse_datetime(payload.get("finished_at"))
    remote_finish_reason = normalize_finish_reason(payload.get("finish_reason"))

    if remote_runs is None and remote_finished_at is None and remote_finish_reason == FinishReason.REASON_NONE:
        logger.info("QUEUE: poll pending queue_id=%s job_id=%s attempt=%s", entry_id, ctx.job_id, count + 1)
        _poll_counts[entry_id] = count + 1
        return

    await asyncio.to_thread(_finalize_resolved, entry_id, ctx.job_id, payload)
    _poll_counts.pop(entry_id, None)


async def run_poll_tick(client: httpx.AsyncClient) -> None:
    entry_ids = await asyncio.to_thread(_fetch_pending_ids)
    if not entry_ids:
        return
    await asyncio.gather(*[poll_entry(client, entry_id) for entry_id in entry_ids])
