import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.api import api_router
from app.api.workers.queue import run_poll_worker, run_submit_worker
from app.api.workers.sync import run_sync_worker
from app.core.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    stop_event = asyncio.Event()
    tasks: list[asyncio.Task] = []

    if settings.EXPERIMENT_QUEUE_WORKER_ENABLED:
        tasks += [
            asyncio.create_task(run_submit_worker(stop_event)),
            asyncio.create_task(run_poll_worker(stop_event)),
        ]
    else:
        logger.info("Experiment queue worker disabled")

    if settings.SERVER_SYNC_WORKER_ENABLED:
        tasks.append(asyncio.create_task(run_sync_worker(stop_event)))
    else:
        logger.info("Server sync worker disabled")

    yield

    stop_event.set()
    if tasks:
        await asyncio.gather(*tasks)


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    method = request.scope.get("method", "websocket")
    path = request.scope.get("path", str(request.url.path))
    client = request.client.host if request.client else "unknown"
    logger.error(
        "HTTPException: %s %s | Method: %s | URL: %s | Client: %s",
        exc.status_code, exc.detail, method, path, client,
    )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
