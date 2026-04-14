import asyncio
import logging
from datetime import datetime, timedelta

import httpx
from pydantic import ValidationError
from sqlalchemy import or_
from sqlmodel import Session, col, select

from app.api.dependencies import engine
from app.api.endpoints.server import resolve_url
from app.core.config import settings
from app.models.experiment import ExperimentQueuePayload
from app.models.experiment_log import ExperimentLog, FinishReason
from app.models.experiment_queue import ExperimentQueue, QueueStatus
from app.models.reservation import Reservation
from app.models.server import Server
from app.models.utils import now

logger = logging.getLogger(__name__)


def _queue_now() -> datetime:
    # Queue timestamps are stored as timestamp without timezone.
    return now().replace(tzinfo=None)


def _parse_datetime(raw: object) -> datetime | None:
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw
    if not isinstance(raw, str):
        return None

    normalized = raw.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _normalize_finish_reason(raw: object) -> FinishReason:
    if not isinstance(raw, str):
        return FinishReason.REASON_NONE

    normalized = raw.strip().lower()
    mapped = {
        "reason_none": FinishReason.REASON_NONE,
        "n/a": FinishReason.REASON_NONE,
        "none": FinishReason.REASON_NONE,
        "user_stop": FinishReason.USER_STOP,
        "simulation_time_reached": FinishReason.SIM_TIME_REACHED,
        "sim_time_reached": FinishReason.SIM_TIME_REACHED,
        "device_timeout": FinishReason.DEVICE_TIMEOUT,
        "timedout": FinishReason.DEVICE_TIMEOUT,
        "timeout": FinishReason.DEVICE_TIMEOUT,
        "exception": FinishReason.EXCEPTION_ERROR,
        "exception_error": FinishReason.EXCEPTION_ERROR,
    }
    return mapped.get(normalized, FinishReason.REASON_NONE)


def _calculate_next_retry(attempts: int) -> datetime:
    retry_base_seconds = max(1, settings.EXPERIMENT_QUEUE_RETRY_BASE_SECONDS)
    retry_max_seconds = max(retry_base_seconds, settings.EXPERIMENT_QUEUE_RETRY_MAX_SECONDS)
    delay_seconds = min(retry_base_seconds * (2 ** max(0, attempts - 1)), retry_max_seconds)
    return _queue_now() + timedelta(seconds=delay_seconds)


def _is_device_reserved(session: Session, device_id: int) -> datetime | None:
    current_time = now()
    stmt = (
        select(Reservation)
        .where(
            Reservation.device_id == device_id,
            Reservation.start <= current_time,
            Reservation.end >= current_time,
        )
        .order_by(col(Reservation.end))
    )
    active_reservation = session.exec(stmt).first()
    if active_reservation is None:
        return None
    return active_reservation.end


def _queue_for_retry(queue_entry: ExperimentQueue) -> None:
    queue_entry.status = QueueStatus.NOT_STARTED
    queue_entry.attempts += 1
    queue_entry.next_attempt_at = _calculate_next_retry(queue_entry.attempts)
    queue_entry.modified_at = _queue_now()


def _payload_json_for_submit(queue_entry: ExperimentQueue) -> dict:
    raw_payload = queue_entry.payload

    if isinstance(raw_payload, ExperimentQueuePayload):
        return raw_payload.model_dump(mode="json")

    normalized_payload = ExperimentQueuePayload.model_validate(raw_payload)
    queue_entry.payload = normalized_payload
    return normalized_payload.model_dump(mode="json")


def _submit_queue_entry(
    session: Session,
    client: httpx.Client,
    queue_entry: ExperimentQueue,
) -> None:
    db_server = session.get(Server, queue_entry.server_id)
    if db_server is None or not (db_server.available and db_server.enabled and db_server.production):
        _queue_for_retry(queue_entry)
        return

    reservation_end = _is_device_reserved(session, queue_entry.device_id)
    if reservation_end is not None:
        queue_entry.status = QueueStatus.NOT_STARTED
        queue_entry.next_attempt_at = reservation_end.replace(tzinfo=None)
        queue_entry.modified_at = _queue_now()
        return

    base_url = resolve_url(db_server)
    if not base_url:
        _queue_for_retry(queue_entry)
        return

    submit_url = f"{base_url}{settings.EXPERIMENT_QUEUE_SUBMIT_PATH}"
    try:
        payload_json = _payload_json_for_submit(queue_entry)
    except ValidationError:
        logger.exception("Queue payload validation failed for queue entry %s", queue_entry.id)
        _queue_for_retry(queue_entry)
        return

    try:
        response = client.post(
            submit_url,
            json=payload_json,
            headers={"x-api-key": settings.EXPERIMENTAL_API_KEY},
        )
    except httpx.RequestError:
        _queue_for_retry(queue_entry)
        return

    if response.status_code == 202:
        try:
            body = response.json()
        except ValueError:
            _queue_for_retry(queue_entry)
            return

        raw_job_id = body.get("job_id")
        if not raw_job_id:
            _queue_for_retry(queue_entry)
            return

        queue_entry.job_id = str(raw_job_id)
        queue_entry.status = QueueStatus.PENDING
        queue_entry.next_attempt_at = _queue_now() + timedelta(seconds=settings.EXPERIMENT_QUEUE_POLL_INTERVAL_SECONDS)
        queue_entry.modified_at = _queue_now()

        db_exp_log = session.get(ExperimentLog, queue_entry.experiment_log_id)
        if db_exp_log is not None and db_exp_log.started_at is None:
            db_exp_log.started_at = now()
            db_exp_log.modified_at = now()
        return

    if response.status_code in {400, 404, 409, 503}:
        _queue_for_retry(queue_entry)
        return

    if response.status_code >= 500:
        _queue_for_retry(queue_entry)
        return

    _queue_for_retry(queue_entry)


def _poll_queue_entry(
    session: Session,
    client: httpx.Client,
    queue_entry: ExperimentQueue,
) -> None:
    if not queue_entry.job_id:
        _queue_for_retry(queue_entry)
        return

    db_server = session.get(Server, queue_entry.server_id)
    if db_server is None:
        queue_entry.next_attempt_at = _queue_now() + timedelta(seconds=settings.EXPERIMENT_QUEUE_POLL_INTERVAL_SECONDS)
        queue_entry.modified_at = _queue_now()
        return

    base_url = resolve_url(db_server)
    if not base_url:
        queue_entry.next_attempt_at = _queue_now() + timedelta(seconds=settings.EXPERIMENT_QUEUE_POLL_INTERVAL_SECONDS)
        queue_entry.modified_at = _queue_now()
        return

    status_path = settings.EXPERIMENT_QUEUE_STATUS_PATH.format(job_id=queue_entry.job_id)
    status_url = f"{base_url}{status_path}"

    try:
        response = client.get(
            status_url,
            headers={"x-api-key": settings.EXPERIMENTAL_API_KEY},
        )
    except httpx.RequestError:
        queue_entry.next_attempt_at = _queue_now() + timedelta(seconds=settings.EXPERIMENT_QUEUE_POLL_INTERVAL_SECONDS)
        queue_entry.modified_at = _queue_now()
        return

    if response.status_code != 200:
        queue_entry.next_attempt_at = _queue_now() + timedelta(seconds=settings.EXPERIMENT_QUEUE_POLL_INTERVAL_SECONDS)
        queue_entry.modified_at = _queue_now()
        return

    try:
        payload = response.json()
    except ValueError:
        queue_entry.next_attempt_at = _queue_now() + timedelta(seconds=settings.EXPERIMENT_QUEUE_POLL_INTERVAL_SECONDS)
        queue_entry.modified_at = _queue_now()
        return

    remote_runs = payload.get("run")
    if remote_runs is None:
        remote_runs = payload.get("runs")
    remote_started_at = _parse_datetime(payload.get("started_at"))
    remote_finished_at = _parse_datetime(payload.get("finished_at"))
    remote_finish_reason = _normalize_finish_reason(payload.get("finish_reason"))

    db_exp_log = session.get(ExperimentLog, queue_entry.experiment_log_id)
    if db_exp_log is not None and db_exp_log.started_at is None:
        db_exp_log.started_at = remote_started_at or now()
        db_exp_log.modified_at = now()

    if remote_runs is None and remote_finished_at is None and remote_finish_reason == FinishReason.REASON_NONE:
        queue_entry.next_attempt_at = _queue_now() + timedelta(seconds=settings.EXPERIMENT_QUEUE_POLL_INTERVAL_SECONDS)
        queue_entry.modified_at = _queue_now()
        return

    if db_exp_log is not None:
        if remote_finished_at is not None:
            db_exp_log.finished_at = remote_finished_at
        db_exp_log.finish_reason = remote_finish_reason
        db_exp_log.run = remote_runs
        db_exp_log.modified_at = now()

    if remote_finish_reason in {FinishReason.EXCEPTION_ERROR, FinishReason.DEVICE_TIMEOUT}:
        queue_entry.status = QueueStatus.FAILED
    else:
        queue_entry.status = QueueStatus.FINISHED

    queue_entry.next_attempt_at = None
    queue_entry.modified_at = _queue_now()


def process_experiment_queue_tick() -> None:
    current_time = _queue_now()

    with Session(engine) as session:
        submit_stmt = (
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

        poll_stmt = (
            select(ExperimentQueue)
            .where(
                ExperimentQueue.status == QueueStatus.PENDING,
                or_(
                    col(ExperimentQueue.next_attempt_at).is_(None),
                    col(ExperimentQueue.next_attempt_at) <= current_time,
                ),
            )
            .order_by(col(ExperimentQueue.created_at))
            .limit(settings.EXPERIMENT_QUEUE_BATCH_SIZE)
        )

        to_submit = session.exec(submit_stmt).all()
        to_poll = session.exec(poll_stmt).all()

        if not to_submit and not to_poll:
            return

        with httpx.Client(timeout=settings.EXPERIMENT_QUEUE_REQUEST_TIMEOUT_SECONDS) as client:
            for queue_entry in to_submit:
                _submit_queue_entry(session, client, queue_entry)

            for queue_entry in to_poll:
                _poll_queue_entry(session, client, queue_entry)

        session.commit()


async def run_experiment_queue_worker(stop_event: asyncio.Event) -> None:
    logger.info("Experiment queue worker started")

    while not stop_event.is_set():
        try:
            process_experiment_queue_tick()
        except Exception:
            logger.exception("Experiment queue worker tick failed")

        try:
            await asyncio.wait_for(
                stop_event.wait(),
                timeout=settings.EXPERIMENT_QUEUE_WORKER_INTERVAL_SECONDS,
            )
        except asyncio.TimeoutError:
            pass

    logger.info("Experiment queue worker stopped")
