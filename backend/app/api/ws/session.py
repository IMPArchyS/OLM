import asyncio
import json
import logging
from contextlib import suppress
from dataclasses import dataclass
from json import JSONDecodeError
from threading import Lock

from fastapi import WebSocket, WebSocketDisconnect, status
from sqlmodel import Session, select
from websockets import connect
from websockets.exceptions import ConnectionClosed

from app.api.dependencies import engine
from app.core.config import settings
from app.models.experiment import Command
from app.models.reservation import Reservation
from app.models.utils import now
from app.api.ws.log_sync import (
    _PendingExperimentLogIds,
    _create_experiment_log_for_payload,
    _delete_experiment_log,
    _mark_experiment_log_as_error,
    _sync_log_from_upstream_message,
)
from app.api.ws.payload import _resolve_device_name_from_payload, _to_experiment_queue_payload
from app.api.ws.stream_buffer import (
    _append_stream_sample,
    _clear_stream_buffer,
    _extract_partial_stream_sample,
)


logger = logging.getLogger(__name__)

_reservation_sessions_lock = Lock()
_reservation_sessions: dict[int, "_ReservationUpstreamSession"] = {}


@dataclass
class _ReservationContext:
    reservation_id: int
    user_id: int
    device_id: int
    device_name: str
    server_id: int
    api_url: str


@dataclass
class _QueuedCommand:
    payload_json: str
    command: Command
    experiment_log_id: int | None


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


class _ReservationUpstreamSession:
    def __init__(self, ctx: _ReservationContext) -> None:
        self.reservation_id = ctx.reservation_id
        self.user_id = ctx.user_id
        self.reservation_device_id = ctx.device_id
        self.reservation_device_name = ctx.device_name
        self.server_id = ctx.server_id
        self.api_url = ctx.api_url

        self.device_name_cache: dict[int, str] = {ctx.device_id: ctx.device_name}
        self.pending_log_ids = _PendingExperimentLogIds()
        self.pending_start_attempt_ids = _PendingExperimentLogIds()
        self.last_sent_command: Command | None = None

        self.command_queue: asyncio.Queue[_QueuedCommand] = asyncio.Queue()
        self.client: WebSocket | None = None
        self.stop_event = asyncio.Event()
        self.runner_task: asyncio.Task[None] | None = None
        self.closed = False

    def start(self) -> None:
        if self.runner_task is not None and not self.runner_task.done():
            return

        self.runner_task = asyncio.create_task(self._run())

    async def set_client(self, ws: WebSocket) -> bool:
        if self.client is not None:
            return False

        self.client = ws
        with suppress(Exception):
            await ws.send_text("Connected, reservation is ok")
        return True

    async def clear_client(self, ws: WebSocket) -> None:
        if self.client is ws:
            self.client = None

    async def _send_text(self, message: str) -> None:
        if self.client is not None:
            with suppress(Exception):
                await self.client.send_text(message)

    async def _send_bytes(self, data: bytes) -> None:
        if self.client is not None:
            with suppress(Exception):
                await self.client.send_bytes(data)

    async def _close_client(self, close_code: int, close_reason: str) -> None:
        if self.client is not None:
            with suppress(Exception):
                await self.client.close(code=close_code, reason=close_reason)
            self.client = None

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

            requested_simulation_seconds = normalized_payload.simulation_time
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

        await self.command_queue.put(_QueuedCommand(
            payload_json=normalized_payload.model_dump_json(),
            command=normalized_payload.command,
            experiment_log_id=experiment_log_id,
        ))

    async def _run_sender(self, upstream_ws) -> None:
        while not self.stop_event.is_set():
            queued = await self.command_queue.get()

            try:
                await upstream_ws.send(queued.payload_json)
                self.last_sent_command = queued.command
            except Exception:
                if queued.experiment_log_id is not None:
                    _mark_experiment_log_as_error(queued.experiment_log_id)
                raise

            if queued.command == Command.START and queued.experiment_log_id is not None:
                self.pending_start_attempt_ids.push(queued.experiment_log_id)

    async def _run_receiver(self, upstream_ws) -> None:
        async for message in upstream_ws:
            if isinstance(message, bytes):
                await self._send_bytes(message)
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

                    await self._send_text(message)
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
            await self._send_text(message)

    async def _run_reservation_watch(self, upstream_ws) -> None:
        while not self.stop_event.is_set():
            reservation_active, reservation_reason = _reservation_state(self.reservation_id)
            if not reservation_active:
                self.stop_event.set()

                with suppress(Exception):
                    await upstream_ws.close(code=status.WS_1000_NORMAL_CLOSURE, reason=reservation_reason)

                await self._send_text(reservation_reason)
                await self._close_client(
                    close_code=status.WS_1008_POLICY_VIOLATION,
                    close_reason=reservation_reason,
                )
                return

            await asyncio.sleep(1)

    async def _run(self) -> None:
        try:
            reservation_active, reservation_reason = _reservation_state(self.reservation_id)
            if not reservation_active:
                await self._send_text(reservation_reason)
                await self._close_client(
                    close_code=status.WS_1008_POLICY_VIOLATION,
                    close_reason=reservation_reason,
                )
                return

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
                logger.warning("Device server connection lost: %s", e)
                await self._send_text(f"Device server connection lost: {e}")
                await self._close_client(
                    close_code=status.WS_1011_INTERNAL_ERROR,
                    close_reason="device server connection lost",
                )
            except Exception as e:
                logger.exception("Device server connection failed: %s", self.api_url)
                await self._send_text(f"Device server unavailable: {e}")
                await self._close_client(
                    close_code=status.WS_1011_INTERNAL_ERROR,
                    close_reason="device server unavailable",
                )
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


def _get_or_create_reservation_session(ctx: _ReservationContext) -> _ReservationUpstreamSession:
    # double-checked locking — create once per reservation_id
    with _reservation_sessions_lock:
        existing = _reservation_sessions.get(ctx.reservation_id)
        if existing is not None and not existing.closed:
            return existing

    new_session = _ReservationUpstreamSession(ctx)

    with _reservation_sessions_lock:
        existing = _reservation_sessions.get(ctx.reservation_id)
        if existing is not None and not existing.closed:
            return existing

        _reservation_sessions[ctx.reservation_id] = new_session

    new_session.start()
    return new_session
