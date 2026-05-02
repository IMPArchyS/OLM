from datetime import datetime, timedelta

from sqlmodel import Session, col, select

from app.core.config import settings
from app.models.device import Device
from app.models.experiment_log import FinishReason
from app.models.experiment_queue import ExperimentQueue, QueueStatus
from app.models.reservation import Reservation
from app.models.utils import now


def queue_now() -> datetime:
    return now().replace(tzinfo=None)


def parse_datetime(raw: object) -> datetime | None:
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw
    if not isinstance(raw, str):
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def normalize_finish_reason(raw: object) -> FinishReason:
    if not isinstance(raw, str):
        return FinishReason.REASON_NONE
    mapping = {
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
    return mapping.get(raw.strip().lower(), FinishReason.REASON_NONE)


def calculate_next_retry(attempts: int) -> datetime:
    base = max(1, settings.EXPERIMENT_QUEUE_RETRY_BASE_SECONDS)
    cap = max(base, settings.EXPERIMENT_QUEUE_RETRY_MAX_SECONDS)
    delay = min(base * (2 ** max(0, attempts - 1)), cap)
    return queue_now() + timedelta(seconds=delay)


def mark_retry_or_fail(entry: ExperimentQueue) -> None:
    entry.attempts += 1
    if entry.attempts >= settings.EXPERIMENT_QUEUE_MAX_SUBMIT_ATTEMPTS:
        entry.status = QueueStatus.FAILED
        entry.next_attempt_at = None
    else:
        entry.status = QueueStatus.NOT_STARTED
        entry.next_attempt_at = calculate_next_retry(entry.attempts)
    entry.modified_at = queue_now()


def _intervals_overlap(
    start_a: datetime, end_a: datetime, start_b: datetime, end_b: datetime
) -> bool:
    return start_a < end_b and start_b < end_a


def maintenance_overlap_end(
    device: Device, run_start: datetime, run_end: datetime
) -> datetime | None:
    ms, me = device.maintenance_start, device.maintenance_end
    if ms is None or me is None:
        return None
    day_count = int(max(1, (run_end - run_start).total_seconds() // 86400 + 2))
    for offset in range(-1, day_count + 1):
        base = (run_start + timedelta(days=offset)).date()
        ws = datetime.combine(base, ms, tzinfo=run_start.tzinfo)
        we = datetime.combine(
            base if ms <= me else base + timedelta(days=1),
            me,
            tzinfo=run_start.tzinfo,
        )
        if _intervals_overlap(run_start, run_end, ws, we):
            return we
    return None


def find_overlapping_reservation(
    session: Session, device_id: int, run_start: datetime, run_end: datetime
) -> Reservation | None:
    stmt = (
        select(Reservation)
        .where(
            Reservation.device_id == device_id,
            Reservation.start < run_end,
            Reservation.end > run_start,
        )
        .order_by(col(Reservation.start))
    )
    return session.exec(stmt).first()
