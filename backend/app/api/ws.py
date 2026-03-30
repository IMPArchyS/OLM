import asyncio
import json
import logging
from json import JSONDecodeError
from contextlib import suppress

from pydantic import ValidationError
from sqlmodel import Session, select, asc

from app.api.dependencies import CurrentUserIdWs, DbSession, engine
from app.api.endpoints.server import resolve_url
from app.core.config import settings
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from websockets import connect
from websockets.exceptions import ConnectionClosed

from app.models.device import Device
from app.models.experiment import ExperimentQueue
from app.models.reservation import Reservation
from app.models.utils import now


ws_router = APIRouter()
logger = logging.getLogger(__name__)


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
) -> str:
    raw_device_id = payload.get("device_id")
    if raw_device_id is None:
        raise ValueError("device_id is required")

    try:
        device_id = int(raw_device_id)
    except (TypeError, ValueError):
        raise ValueError("device_id must be an integer")

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


def _to_experiment_queue_payload(payload: object, resolved_device_name: str) -> str:
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")

    candidate = dict(payload)
    candidate.pop("device_id", None)
    candidate["device_name"] = resolved_device_name

    normalized = ExperimentQueue.model_validate(candidate)
    return normalized.model_dump_json()


async def _client_to_upstream(
    client_ws: WebSocket,
    upstream_ws,
):
    device_name_cache: dict[int, str] = {}

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
            )
            normalized_payload = _to_experiment_queue_payload(payload, resolved_device_name)
        except (ValidationError, ValueError) as e:
            with suppress(Exception):
                await upstream_ws.close(code=status.WS_1000_NORMAL_CLOSURE, reason="invalid experiment payload")
            with suppress(Exception):
                await client_ws.close(code=status.WS_1003_UNSUPPORTED_DATA, reason=f"invalid experiment payload: {e}")
            break

        await upstream_ws.send(normalized_payload)


async def _upstream_to_client(upstream_ws, client_ws: WebSocket):
    async for msg in upstream_ws:
        if isinstance(msg, bytes):
            await client_ws.send_bytes(msg)
        else:
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
    
    stmt = select(Reservation).where(
        Reservation.user_id == user_id,
        Reservation.start <= now(), 
        Reservation.end >= now()
    ).order_by(asc(Reservation.start))
    db_reservation = db.exec(stmt).first()
    
    if not db_reservation:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="no reservation for user")
        return

    reservation_id = db_reservation.id
    if reservation_id is None:
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="reservation id missing")
        return

    await websocket.send_text("Connected, reservation is ok")
    
    base_url = resolve_url(db_reservation.device.server)
    if not base_url:
        await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA, reason="no server api domain found")
        return
    
    api_url = _to_websocket_url(base_url, "/ws/server/experiment")
    
    try:
        async with connect(
            api_url,
            additional_headers={"x-api-key": settings.EXPERIMENTAL_API_KEY},
        ) as exp_ws:
            to_upstream = asyncio.create_task(
                _client_to_upstream(websocket, exp_ws)
            )
            to_client = asyncio.create_task(_upstream_to_client(exp_ws, websocket))
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