import asyncio
import json
import logging
from threading import Lock
from collections import deque
from datetime import datetime
from json import JSONDecodeError
from contextlib import suppress
from typing import Any

from pydantic import ValidationError
from sqlmodel import Session, select, asc

from app.api.dependencies import CurrentUserId, CurrentUserIdWs, DbSession, engine
from app.api.endpoints.server import resolve_url
from app.core.config import settings
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from websockets import connect
from websockets.exceptions import ConnectionClosed

from app.models.device import Device
from app.models.experiment import Command, Experiment, ExperimentQueuePayload
from app.models.experiment_log import ExperimentLog, FinishReason
from app.models.reservation import Reservation
from app.models.utils import now


ws_router = APIRouter()
logger = logging.getLogger(__name__)

_stream_buffer_lock = Lock()
_stream_buffers: dict[int, list[dict[str, Any]]] = {}


class _PendingExperimentLogIds:
    def __init__(self) -> None:
        self._ids: deque[int] = deque()

    def push(self, experiment_log_id: int) -> None:
        self._ids.append(experiment_log_id)

    def pop(self) -> int | None:
        if not self._ids:
            return None
        return self._ids.popleft()


def _clear_stream_buffer(reservation_id: int) -> None:
    with _stream_buffer_lock:
        _stream_buffers[reservation_id] = []


def _append_stream_sample(reservation_id: int, sample: dict[str, Any]) -> None:
    with _stream_buffer_lock:
        entries = _stream_buffers.setdefault(reservation_id, [])
        entries.append(sample)

        max_samples = max(1, settings.EXPERIMENT_WS_BUFFER_MAX_SAMPLES)
        overflow = len(entries) - max_samples
        if overflow > 0:
            del entries[:overflow]


def _read_stream_samples(
    reservation_id: int,
    after_index: int,
) -> tuple[list[dict[str, Any]], int, int]:
    with _stream_buffer_lock:
        entries = _stream_buffers.get(reservation_id, [])
        total = len(entries)
        safe_after_index = min(max(after_index, 0), total)
        samples = entries[safe_after_index:]
        next_index = total

    return samples, next_index, total


def _extract_partial_stream_sample(payload: dict[str, Any]) -> dict[str, Any] | None:
    if "error" in payload:
        return None

    if "run" in payload or "runs" in payload:
        return None

    if "finished_at" in payload or "finish_reason" in payload:
        return None

    if "time" not in payload:
        return None

    return payload


def _get_current_reservation(db: DbSession, user_id: int) -> Reservation | None:
    stmt = select(Reservation).where(
        Reservation.user_id == user_id,
        Reservation.start <= now(),
        Reservation.end >= now(),
    ).order_by(asc(Reservation.start))
    return db.exec(stmt).first()


def _to_websocket_url(base_url: str, path: str) -> str:
    normalized_path = path if path.startswith("/") else f"/{path}"

    if base_url.startswith("https://"):
        return f"wss://{base_url[len('https://'):]}{normalized_path}"
    if base_url.startswith("http://"):
        return f"ws://{base_url[len('http://'):]}{normalized_path}"
    if base_url.startswith("wss://") or base_url.startswith("ws://"):
        return f"{base_url}{normalized_path}"

    return f"ws://{base_url}{normalized_path}"


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
        db_device_name = session.exec(
            select(Device.name).where(Device.id == device_id)
        ).first()

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

    normalized = ExperimentQueuePayload.model_validate(candidate)
    if normalized.command != Command.START:
        raise ValueError("command must be start")
    return normalized


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
            raise ValueError(
                f"device {reservation_device_id} is not assigned to experiment {experiment_id}"
            )

        db_experiment_log = ExperimentLog(
            user_id=user_id,
            experiment_id=experiment_id,
            device_id=reservation_device_id,
            server_id=server_id,
            started_at=now(),
            finished_at=None,
            run=None,
            note=None,
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

    has_terminal_payload = (
        remote_runs is not None
        or remote_finished_at is not None
        or remote_finish_reason != FinishReason.REASON_NONE
    )
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

    # Upstream sends {"error": "..."} for rejected START requests.
    # Those requests already created pending ExperimentLog entries locally,
    # so close one pending log as failed to avoid orphan open rows.
    if "error" in payload:
        rejected_log_id = pending_log_ids.pop()
        if rejected_log_id is not None:
            _delete_experiment_log(rejected_log_id)
        return

    _sync_next_log_with_terminal_payload(pending_log_ids, payload)


@ws_router.get("/reservation/current/stream-buffer")
def get_current_stream_buffer(
    db: DbSession,
    user_id: CurrentUserId,
    after_index: int = Query(default=0, ge=0),
):
    db_reservation = _get_current_reservation(db, user_id)
    if db_reservation is None or db_reservation.id is None:
        return {
            "reservation_id": None,
            "samples": [],
            "next_index": after_index,
            "total": 0,
        }

    samples, next_index, total = _read_stream_samples(db_reservation.id, after_index)
    return {
        "reservation_id": db_reservation.id,
        "samples": samples,
        "next_index": next_index,
        "total": total,
    }


async def _client_to_upstream(
    client_ws: WebSocket,
    upstream_ws,
    user_id: int,
    reservation_id: int,
    reservation_device_id: int,
    reservation_device_name: str,
    server_id: int,
    pending_log_ids: _PendingExperimentLogIds,
):
    device_name_cache: dict[int, str] = {reservation_device_id: reservation_device_name}

    while True:
        msg = await client_ws.receive()

        msg_type = msg.get("type")
        if msg_type == "websocket.disconnect":
            break

        text = msg.get("text")
        data = msg.get("bytes")

        raw_payload = text
        if raw_payload is None and data is not None:
            try:
                raw_payload = data.decode("utf-8")
            except UnicodeDecodeError:
                with suppress(Exception):
                    await upstream_ws.close(code=status.WS_1000_NORMAL_CLOSURE, reason="invalid json payload")
                with suppress(Exception):
                    await client_ws.close(code=status.WS_1003_UNSUPPORTED_DATA, reason="payload must be utf-8 json")
                break

        if raw_payload is None:
            continue

        try:
            payload = json.loads(raw_payload)
        except JSONDecodeError:
            with suppress(Exception):
                await upstream_ws.close(code=status.WS_1000_NORMAL_CLOSURE, reason="invalid json payload")
            with suppress(Exception):
                await client_ws.close(code=status.WS_1003_UNSUPPORTED_DATA, reason="payload must be valid json")
            break

        try:
            if not isinstance(payload, dict):
                raise ValueError("payload must be a JSON object")

            resolved_device_name = _resolve_device_name_from_payload(
                payload,
                device_name_cache,
                reservation_device_id,
            )
            normalized_payload = _to_experiment_queue_payload(payload, resolved_device_name)
            experiment_log_id = _create_experiment_log_for_payload(
                normalized_payload,
                user_id,
                reservation_device_id,
                server_id,
            )
        except (ValidationError, ValueError) as e:
            with suppress(Exception):
                await upstream_ws.close(code=status.WS_1000_NORMAL_CLOSURE, reason="invalid experiment payload")
            with suppress(Exception):
                await client_ws.close(code=status.WS_1003_UNSUPPORTED_DATA, reason=f"invalid experiment payload: {e}")
            break

        try:
            await upstream_ws.send(normalized_payload.model_dump_json())
            _clear_stream_buffer(reservation_id)
            pending_log_ids.push(experiment_log_id)
        except Exception:
            _mark_experiment_log_as_error(experiment_log_id)
            raise


async def _upstream_to_client(
    upstream_ws,
    client_ws: WebSocket,
    reservation_id: int,
    pending_log_ids: _PendingExperimentLogIds,
):
    async for msg in upstream_ws:
        if isinstance(msg, bytes):
            await client_ws.send_bytes(msg)
        else:
            try:
                payload = json.loads(msg)
            except JSONDecodeError:
                payload = None

            if isinstance(payload, dict):
                partial_sample = _extract_partial_stream_sample(payload)
                if partial_sample is not None:
                    _append_stream_sample(reservation_id, partial_sample)

            _sync_log_from_upstream_message(pending_log_ids, msg)
            await client_ws.send_text(msg)


async def _close_on_reservation_end_or_delete(
    reservation_id: int,
    client_ws: WebSocket,
    upstream_ws,
):
    while True:
        with Session(engine) as session:
            reservation_end = session.exec(
                select(Reservation.end).where(Reservation.id == reservation_id)
            ).first()

        if reservation_end is None:
            with suppress(Exception):
                await upstream_ws.close(
                    code=status.WS_1000_NORMAL_CLOSURE,
                    reason="reservation deleted",
                )
            with suppress(Exception):
                await client_ws.close(
                    code=status.WS_1008_POLICY_VIOLATION,
                    reason="reservation deleted",
                )
            return

        if reservation_end <= now():
            with suppress(Exception):
                await upstream_ws.close(
                    code=status.WS_1000_NORMAL_CLOSURE,
                    reason="reservation expired",
                )
            with suppress(Exception):
                await client_ws.close(
                    code=status.WS_1008_POLICY_VIOLATION,
                    reason="reservation expired",
                )
            return

        await asyncio.sleep(1)


@ws_router.websocket("/reservation/current")
async def reservation_proxy(db: DbSession, websocket: WebSocket, user_id: CurrentUserIdWs):
    await websocket.accept()

    db_reservation = _get_current_reservation(db, user_id)
    
    if not db_reservation:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="no reservation for user")
        return

    reservation_id = db_reservation.id
    if reservation_id is None:
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="reservation id missing")
        return

    db_device = db_reservation.device
    if db_device is None or db_device.id is None:
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="reservation device missing")
        return

    db_server = db_device.server
    if db_server is None or db_server.id is None:
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="reservation server missing")
        return

    if not (db_server.available and db_server.enabled and db_server.production):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="server unavailable")
        return

    await websocket.send_text("Connected, reservation is ok")
    
    base_url = resolve_url(db_server)
    if not base_url:
        await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA, reason="no server api domain found")
        return
    
    api_url = _to_websocket_url(base_url, settings.EXPERIMENT_WS_PATH)
    pending_log_ids = _PendingExperimentLogIds()
    
    try:
        async with connect(
            api_url,
            additional_headers={"x-api-key": settings.EXPERIMENTAL_API_KEY},
        ) as exp_ws:
            to_upstream = asyncio.create_task(
                _client_to_upstream(
                    websocket,
                    exp_ws,
                    user_id,
                    reservation_id,
                    db_device.id,
                    db_device.name,
                    db_server.id,
                    pending_log_ids,
                )
            )
            to_client = asyncio.create_task(_upstream_to_client(exp_ws, websocket, reservation_id, pending_log_ids))
            reservation_watch = asyncio.create_task(
                _close_on_reservation_end_or_delete(reservation_id, websocket, exp_ws)
            )

            done, pending = await asyncio.wait(
                {to_upstream, to_client, reservation_watch},
                return_when=asyncio.FIRST_COMPLETED,
            )

            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)

            for task in done:
                task.result()
    except WebSocketDisconnect:
        pass
    except ConnectionClosed:
        pass
    except Exception as e:
        logger.exception("Upstream websocket connection failed: %s", api_url)
        with suppress(Exception):
            await websocket.send_text(f"Upstream websocket unavailable: {e}")
    finally:
        with suppress(Exception):
            await websocket.close()