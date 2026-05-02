from datetime import datetime

from sqlmodel import Session, select

from app.api.dependencies import engine
from app.models.device import Device
from app.models.experiment import ExperimentQueuePayload
from app.models.experiment_log import FinishReason


def _resolve_device_name_from_payload(
    payload: dict,
    device_name_cache: dict[int, str],
    reservation_device_id: int,
) -> str:
    raw_device_id = payload.get("device_id")
    if raw_device_id is None:
        raise ValueError("device_id is required")

    try:
        device_id = int(raw_device_id)
    except (TypeError, ValueError):
        raise ValueError("device_id must be an integer")

    if device_id != reservation_device_id:
        raise ValueError("device_id must match reserved device")

    if device_id in device_name_cache:
        return device_name_cache[device_id]

    with Session(engine) as session:
        db_device_name = session.exec(select(Device.name).where(Device.id == device_id)).first()

    if not db_device_name:
        raise ValueError(f"device with id {device_id} not found")

    device_name_cache[device_id] = db_device_name
    return db_device_name


def _to_experiment_queue_payload(payload: object, resolved_device_name: str) -> ExperimentQueuePayload:
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")

    candidate = dict(payload)
    candidate.pop("device_id", None)
    candidate["device_name"] = resolved_device_name

    return ExperimentQueuePayload.model_validate(candidate)


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
