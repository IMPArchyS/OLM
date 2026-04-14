import asyncio
import json
import logging
from collections import deque
from contextlib import suppress
from datetime import datetime
from json import JSONDecodeError
from threading import Lock
from typing import Any

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from pydantic import ValidationError
from sqlmodel import Session, asc, select
from websockets import connect
from websockets.exceptions import ConnectionClosed

from app.api.dependencies import CurrentUserId, CurrentUserIdWs, DbSession, engine
from app.api.endpoints.server import resolve_url
from app.core.config import settings
from app.models.device import Device
from app.models.experiment import Command, Experiment, ExperimentQueuePayload
from app.models.experiment_log import ExperimentLog, FinishReason
from app.models.reservation import Reservation
from app.models.utils import now


ws_router = APIRouter()
logger = logging.getLogger(__name__)

_stream_buffer_lock = Lock()
_stream_buffers: dict[int, list[dict[str, Any]]] = {}

_reservation_sessions_lock = Lock()
_reservation_sessions: dict[int, "_ReservationUpstreamSession"] = {}


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
    stmt = (
        select(Reservation)
        .where(
            Reservation.user_id == user_id,
            Reservation.start <= now(),
            Reservation.end >= now(),
        )
        .order_by(asc(Reservation.start))
    )
    return db.exec(stmt).first()


def _reservation_state(reservation_id: int) -> tuple[bool, str]:
    with Session(engine) as session:
        reservation_end = session.exec(select(Reservation.end).where(Reservation.id == reservation_id)).first()

    if reservation_end is None:
        return False, "reservation deleted"

    if reservation_end <= now():
        return False, "reservation expired"

    return True, "reservation active"


def _remaining_reservation_seconds(reservation_id: int) -> float | None:
    with Session(engine) as session:
        reservation_end = session.exec(select(Reservation.end).where(Reservation.id == reservation_id)).first()

    if reservation_end is None:
        return None

    remaining = (reservation_end - now()).total_seconds()
    return max(0.0, remaining)


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


class _ReservationUpstreamSession:
    def __init__(
        self,
        reservation_id: int,
        user_id: int,
        reservation_device_id: int,
        reservation_device_name: str,
        server_id: int,
        api_url: str,
    ) -> None:
        self.reservation_id = reservation_id
        self.user_id = user_id
        self.reservation_device_id = reservation_device_id
        self.reservation_device_name = reservation_device_name
        self.server_id = server_id
        self.api_url = api_url

        self.device_name_cache: dict[int, str] = {reservation_device_id: reservation_device_name}
        self.pending_log_ids = _PendingExperimentLogIds()
        self.pending_start_attempt_ids = _PendingExperimentLogIds()
        self.last_sent_command: Command | None = None

        self.command_queue: asyncio.Queue[tuple[str, Command, int | None]] = asyncio.Queue()
        self.clients: set[WebSocket] = set()
        self.clients_lock = asyncio.Lock()
        self.stop_event = asyncio.Event()
        self.runner_task: asyncio.Task[None] | None = None
        self.closed = False

    def start(self) -> None:
        if self.runner_task is not None and not self.runner_task.done():
            return

        self.runner_task = asyncio.create_task(self._run())

    async def add_client(self, client_ws: WebSocket) -> None:
        async with self.clients_lock:
            self.clients.add(client_ws)

        with suppress(Exception):
            await client_ws.send_text("Connected, reservation is ok")

    async def remove_client(self, client_ws: WebSocket) -> None:
        async with self.clients_lock:
            self.clients.discard(client_ws)

    async def _broadcast_text(self, message: str) -> None:
        async with self.clients_lock:
            clients = list(self.clients)

        if not clients:
            return

        stale: list[WebSocket] = []
        for client in clients:
            try:
                await client.send_text(message)
            except Exception:
                stale.append(client)

        if stale:
            async with self.clients_lock:
                for client in stale:
                    self.clients.discard(client)

    async def _broadcast_bytes(self, payload: bytes) -> None:
        async with self.clients_lock:
            clients = list(self.clients)

        if not clients:
            return

        stale: list[WebSocket] = []
        for client in clients:
            try:
                await client.send_bytes(payload)
            except Exception:
                stale.append(client)

        if stale:
            async with self.clients_lock:
                for client in stale:
                    self.clients.discard(client)

    async def _close_all_clients(self, close_code: int, close_reason: str) -> None:
        async with self.clients_lock:
            clients = list(self.clients)
            self.clients.clear()

        for client in clients:
            with suppress(Exception):
                await client.close(code=close_code, reason=close_reason)

    async def enqueue_client_payload(self, raw_payload: str) -> None:
        try:
            payload = json.loads(raw_payload)
        except JSONDecodeError:
            raise ValueError("payload must be valid json")

        if not isinstance(payload, dict):
            raise ValueError("payload must be a JSON object")

        resolved_device_name = _resolve_device_name_from_payload(
            payload,
            self.device_name_cache,
            self.reservation_device_id,
        )

        normalized_payload = _to_experiment_queue_payload(payload, resolved_device_name)

        experiment_log_id: int | None = None
        if normalized_payload.command == Command.START:
            remaining_seconds = _remaining_reservation_seconds(self.reservation_id)
            if remaining_seconds is None or remaining_seconds <= 0:
                raise ValueError("reservation expired")

            requested_simulation_seconds = float(normalized_payload.simulation_time)
            if requested_simulation_seconds > remaining_seconds:
                raise ValueError(
                    f"simulation_time {requested_simulation_seconds:g}s exceeds remaining reservation window {remaining_seconds:.1f}s"
                )

            experiment_log_id = _create_experiment_log_for_payload(
                normalized_payload,
                self.user_id,
                self.reservation_device_id,
                self.server_id,
            )
            _clear_stream_buffer(self.reservation_id)

        await self.command_queue.put((normalized_payload.model_dump_json(), normalized_payload.command, experiment_log_id))

    async def _run_sender(self, upstream_ws) -> None:
        while not self.stop_event.is_set():
            payload_json, command, experiment_log_id = await self.command_queue.get()

            try:
                await upstream_ws.send(payload_json)
                self.last_sent_command = command
            except Exception:
                if experiment_log_id is not None:
                    _mark_experiment_log_as_error(experiment_log_id)
                raise

            if command == Command.START and experiment_log_id is not None:
                self.pending_start_attempt_ids.push(experiment_log_id)

    async def _run_receiver(self, upstream_ws) -> None:
        async for message in upstream_ws:
            if isinstance(message, bytes):
                await self._broadcast_bytes(message)
                continue

            try:
                payload = json.loads(message)
            except JSONDecodeError:
                payload = None

            if isinstance(payload, dict):
                if "error" in payload:
                    if self.last_sent_command == Command.START:
                        rejected_log_id = self.pending_start_attempt_ids.pop()
                        if rejected_log_id is not None:
                            _delete_experiment_log(rejected_log_id)

                    await self._broadcast_text(message)
                    continue

                has_run_signal = (
                    "time" in payload
                    or "run" in payload
                    or "runs" in payload
                    or "finished_at" in payload
                    or "finish_reason" in payload
                )
                if has_run_signal:
                    accepted_log_id = self.pending_start_attempt_ids.pop()
                    if accepted_log_id is not None:
                        self.pending_log_ids.push(accepted_log_id)

                partial_sample = _extract_partial_stream_sample(payload)
                if partial_sample is not None:
                    _append_stream_sample(self.reservation_id, partial_sample)

            _sync_log_from_upstream_message(self.pending_log_ids, message)
            await self._broadcast_text(message)

    async def _run_reservation_watch(self, upstream_ws) -> None:
        while not self.stop_event.is_set():
            reservation_active, reservation_reason = _reservation_state(self.reservation_id)
            if not reservation_active:
                self.stop_event.set()

                with suppress(Exception):
                    await upstream_ws.close(code=status.WS_1000_NORMAL_CLOSURE, reason=reservation_reason)

                await self._broadcast_text(reservation_reason)
                await self._close_all_clients(
                    close_code=status.WS_1008_POLICY_VIOLATION,
                    close_reason=reservation_reason,
                )
                return

            await asyncio.sleep(1)

    async def _run(self) -> None:
        try:
            while not self.stop_event.is_set():
                reservation_active, reservation_reason = _reservation_state(self.reservation_id)
                if not reservation_active:
                    await self._broadcast_text(reservation_reason)
                    await self._close_all_clients(
                        close_code=status.WS_1008_POLICY_VIOLATION,
                        close_reason=reservation_reason,
                    )
                    break

                try:
                    async with connect(
                        self.api_url,
                        additional_headers={"x-api-key": settings.EXPERIMENTAL_API_KEY},
                    ) as upstream_ws:
                        sender_task = asyncio.create_task(self._run_sender(upstream_ws))
                        receiver_task = asyncio.create_task(self._run_receiver(upstream_ws))
                        reservation_watch_task = asyncio.create_task(self._run_reservation_watch(upstream_ws))

                        done, pending = await asyncio.wait(
                            {sender_task, receiver_task, reservation_watch_task},
                            return_when=asyncio.FIRST_COMPLETED,
                        )

                        for pending_task in pending:
                            pending_task.cancel()
                        await asyncio.gather(*pending, return_exceptions=True)

                        for completed_task in done:
                            completed_task.result()
                except WebSocketDisconnect:
                    pass
                except ConnectionClosed as e:
                    if self.stop_event.is_set():
                        break
                    await self._broadcast_text(f"Upstream websocket closed: {e}")
                except Exception as e:
                    if self.stop_event.is_set():
                        break
                    logger.exception("Upstream websocket connection failed: %s", self.api_url)
                    await self._broadcast_text(f"Upstream websocket unavailable: {e}")

                if not self.stop_event.is_set():
                    await asyncio.sleep(1)
        finally:
            for pending_log_id in self.pending_start_attempt_ids.drain():
                _mark_experiment_log_as_error(pending_log_id)

            for pending_log_id in self.pending_log_ids.drain():
                _mark_experiment_log_as_error(pending_log_id)

            self.closed = True
            _clear_stream_buffer(self.reservation_id)
            _remove_reservation_session(self.reservation_id, expected=self)


def _remove_reservation_session(
    reservation_id: int,
    expected: _ReservationUpstreamSession | None = None,
) -> None:
    with _reservation_sessions_lock:
        current = _reservation_sessions.get(reservation_id)
        if current is None:
            return

        if expected is not None and current is not expected:
            return

        _reservation_sessions.pop(reservation_id, None)


def _get_or_create_reservation_session(
    reservation_id: int,
    user_id: int,
    reservation_device_id: int,
    reservation_device_name: str,
    server_id: int,
    api_url: str,
) -> _ReservationUpstreamSession:
    with _reservation_sessions_lock:
        existing = _reservation_sessions.get(reservation_id)
        if existing is not None and not existing.closed:
            return existing

    new_session = _ReservationUpstreamSession(
        reservation_id=reservation_id,
        user_id=user_id,
        reservation_device_id=reservation_device_id,
        reservation_device_name=reservation_device_name,
        server_id=server_id,
        api_url=api_url,
    )

    with _reservation_sessions_lock:
        existing = _reservation_sessions.get(reservation_id)
        if existing is not None and not existing.closed:
            return existing

        _reservation_sessions[reservation_id] = new_session

    new_session.start()
    return new_session


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


@ws_router.websocket("/reservation/current")
async def reservation_proxy(db: DbSession, websocket: WebSocket, user_id: CurrentUserIdWs):
    await websocket.accept()

    db_reservation = _get_current_reservation(db, user_id)
    if db_reservation is None:
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

    base_url = resolve_url(db_server)
    if not base_url:
        await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA, reason="no server api domain found")
        return

    api_url = _to_websocket_url(base_url, settings.EXPERIMENT_WS_PATH)
    session = _get_or_create_reservation_session(
        reservation_id=reservation_id,
        user_id=user_id,
        reservation_device_id=db_device.id,
        reservation_device_name=db_device.name,
        server_id=db_server.id,
        api_url=api_url,
    )

    await session.add_client(websocket)

    try:
        while True:
            message = await websocket.receive()
            message_type = message.get("type")
            if message_type == "websocket.disconnect":
                break

            raw_payload = message.get("text")
            data_payload = message.get("bytes")

            if raw_payload is None and data_payload is not None:
                try:
                    raw_payload = data_payload.decode("utf-8")
                except UnicodeDecodeError:
                    await websocket.send_text(json.dumps({"error": "payload must be utf-8 json"}))
                    continue

            if raw_payload is None:
                continue

            try:
                await session.enqueue_client_payload(raw_payload)
            except (ValidationError, ValueError) as e:
                await websocket.send_text(json.dumps({"error": f"invalid experiment payload: {e}"}))
    except WebSocketDisconnect:
        pass
    finally:
        await session.remove_client(websocket)
        with suppress(Exception):
            await websocket.close()
