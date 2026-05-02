import json
from contextlib import suppress

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from pydantic import ValidationError
from sqlmodel import asc, select

from app.api.dependencies import AuthUser, CurrentUser, CurrentUserWs, DbSession, PermissionWs
from app.api.endpoints.server import resolve_url
from app.api.ws.session import _ReservationContext, _get_or_create_reservation_session
from app.api.ws.stream_buffer import _read_stream_samples
from app.core.config import settings
from app.models.reservation import Reservation
from app.models.utils import now


ws_router = APIRouter()


def _to_websocket_url(base_url: str, path: str) -> str:
    normalized_path = path if path.startswith("/") else f"/{path}"

    if base_url.startswith("https://"):
        return f"wss://{base_url[len('https://'):]}{normalized_path}"
    if base_url.startswith("http://"):
        return f"ws://{base_url[len('http://'):]}{normalized_path}"
    if base_url.startswith("wss://") or base_url.startswith("ws://"):
        return f"{base_url}{normalized_path}"

    return f"ws://{base_url}{normalized_path}"


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


@ws_router.get("/reservation/current/stream-buffer")
def get_current_stream_buffer(
    db: DbSession,
    user: CurrentUser,
    after_index: int = Query(default=0, ge=0),
):
    db_reservation = _get_current_reservation(db, user.id)
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
async def reservation_proxy(
    db: DbSession,
    websocket: WebSocket,
    user: CurrentUserWs,
    _: AuthUser = PermissionWs("olm.experiment.run"),
):
    await websocket.accept()

    db_reservation = _get_current_reservation(db, user.id)
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

    ctx = _ReservationContext(
        reservation_id=reservation_id,
        user_id=user.id,
        device_id=db_device.id,
        device_name=db_device.name,
        server_id=db_server.id,
        api_url=_to_websocket_url(base_url, settings.EXPERIMENT_WS_PATH),
    )
    session = _get_or_create_reservation_session(ctx)

    if not await session.set_client(websocket):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="already open in another window")
        return

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
        await session.clear_client(websocket)
        with suppress(Exception):
            await websocket.close()
