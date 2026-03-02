import asyncio
from contextlib import suppress

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from websockets import connect
from websockets.exceptions import ConnectionClosed


ws_router = APIRouter()


async def _client_to_upstream(client_ws: WebSocket, upstream_ws):
    while True:
        msg = await client_ws.receive()

        msg_type = msg.get("type")
        if msg_type == "websocket.disconnect":
            break

        text = msg.get("text")
        data = msg.get("bytes")

        if text is not None:
            await upstream_ws.send(text)
        elif data is not None:
            await upstream_ws.send(data)


async def _upstream_to_client(upstream_ws, client_ws: WebSocket):
    async for msg in upstream_ws:
        if isinstance(msg, bytes):
            await client_ws.send_bytes(msg)
        else:
            await client_ws.send_text(msg)


@ws_router.websocket("/test/{experiment_id}")
async def reservation_proxy(websocket: WebSocket, experiment_id: int):
    await websocket.accept()
    upstream_url = f"ws://host.docker.internal:8001/ws/experimental/test"

    try:
        async with connect(upstream_url) as exp_ws:
            to_upstream = asyncio.create_task(_client_to_upstream(websocket, exp_ws))
            to_client = asyncio.create_task(_upstream_to_client(exp_ws, websocket))

            done, pending = await asyncio.wait(
                {to_upstream, to_client},
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
    except Exception:
        with suppress(Exception):
            await websocket.send_text("Upstream websocket unavailable")
    finally:
        with suppress(Exception):
            await websocket.close()