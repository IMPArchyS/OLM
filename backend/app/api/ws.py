from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import websockets


ws_router = APIRouter()

@ws_router.websocket("/reservation/{reservation_id}")
async def reservation_proxy(websocket: WebSocket, reservation_id: int):
    await websocket.accept()

    async with websockets.connect("ws://host.docker.internal:8001/ws/test") as exp_ws:
        async for msg in exp_ws:
            await websocket.send_text(str(msg))