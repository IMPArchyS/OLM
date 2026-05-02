import json
from collections import deque
from json import JSONDecodeError

from sqlmodel import Session, select

from app.api.dependencies import engine
from app.models.experiment import Experiment, ExperimentQueuePayload
from app.models.experiment_log import ExperimentLog, FinishReason
from app.models.utils import now
from app.api.ws.payload import _normalize_finish_reason, _parse_datetime


class _PendingExperimentLogIds:
    def __init__(self) -> None:
        self._ids: deque[int] = deque()

    def push(self, experiment_log_id: int) -> None:
        self._ids.append(experiment_log_id)

    def pop(self) -> int | None:
        if not self._ids:
            return None
        return self._ids.popleft()

    def drain(self) -> list[int]:
        ids = list(self._ids)
        self._ids.clear()
        return ids


def _create_experiment_log_for_payload(
    payload: ExperimentQueuePayload,
    user_id: int,
    reservation_device_id: int,
    server_id: int,
) -> int:
    if payload.user_id != user_id:
        raise ValueError("user_id in payload must match authenticated user")

    experiment_id = int(payload.id)

    with Session(engine) as session:
        db_experiment = session.get(Experiment, experiment_id)
        if db_experiment is None:
            raise ValueError(f"experiment with id {experiment_id} not found")

        if not any(device.id == reservation_device_id for device in db_experiment.devices):
            raise ValueError(f"device {reservation_device_id} is not assigned to experiment {experiment_id}")

        db_experiment_log = ExperimentLog(
            user_id=user_id,
            experiment_id=experiment_id,
            device_id=reservation_device_id,
            server_id=server_id,
            started_at=now(),
            finished_at=None,
            run=None,
        )
        session.add(db_experiment_log)
        session.commit()
        session.refresh(db_experiment_log)

    if db_experiment_log.id is None:
        raise ValueError("failed to create experiment log")

    return db_experiment_log.id


def _mark_experiment_log_as_error(experiment_log_id: int) -> None:
    with Session(engine) as session:
        db_experiment_log = session.get(ExperimentLog, experiment_log_id)
        if db_experiment_log is None:
            return

        db_experiment_log.finish_reason = FinishReason.EXCEPTION_ERROR
        db_experiment_log.finished_at = now()
        db_experiment_log.modified_at = now()
        session.add(db_experiment_log)
        session.commit()


def _delete_experiment_log(experiment_log_id: int) -> None:
    with Session(engine) as session:
        db_experiment_log = session.get(ExperimentLog, experiment_log_id)
        if db_experiment_log is None:
            return

        session.delete(db_experiment_log)
        session.commit()


def _sync_next_log_with_terminal_payload(
    pending_log_ids: _PendingExperimentLogIds,
    payload: dict,
) -> None:
    remote_runs = payload.get("run")
    if remote_runs is None:
        remote_runs = payload.get("runs")

    remote_started_at = _parse_datetime(payload.get("started_at"))
    remote_finished_at = _parse_datetime(payload.get("finished_at"))
    remote_finish_reason = _normalize_finish_reason(payload.get("finish_reason"))

    has_terminal_payload = remote_runs is not None or remote_finished_at is not None or remote_finish_reason != FinishReason.REASON_NONE
    if not has_terminal_payload:
        return

    experiment_log_id = pending_log_ids.pop()
    if experiment_log_id is None:
        return

    with Session(engine) as session:
        db_experiment_log = session.get(ExperimentLog, experiment_log_id)
        if db_experiment_log is None:
            return

        if remote_started_at is not None:
            db_experiment_log.started_at = remote_started_at
        elif db_experiment_log.started_at is None:
            db_experiment_log.started_at = now()

        if remote_finished_at is not None:
            db_experiment_log.finished_at = remote_finished_at

        db_experiment_log.finish_reason = remote_finish_reason
        db_experiment_log.run = remote_runs
        db_experiment_log.modified_at = now()
        session.add(db_experiment_log)
        session.commit()


def _sync_log_from_upstream_message(
    pending_log_ids: _PendingExperimentLogIds,
    raw_message: str,
) -> None:
    try:
        payload = json.loads(raw_message)
    except JSONDecodeError:
        return

    if not isinstance(payload, dict):
        return

    _sync_next_log_with_terminal_payload(pending_log_ids, payload)
