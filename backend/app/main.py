import asyncio

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.api.api import api_router
from app.api.workers.experiment_queue_worker import run_experiment_queue_worker
from app.core.config import settings

logger = logging.getLogger(__name__)

app = FastAPI()
worker_stop_event = asyncio.Event()
worker_task: asyncio.Task | None = None


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    method = request.scope.get("method", "websocket")
    path = request.scope.get("path", str(request.url.path))
    client = request.client.host if request.client else "unknown"

    logger.error(
        f"HTTPException: {exc.status_code} {exc.detail} | "
        f"Method: {method} | "
        f"URL: {path} | "
        f"Client: {client}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.on_event("startup")
async def startup_experiment_queue_worker() -> None:
    global worker_task

    if not settings.EXPERIMENT_QUEUE_WORKER_ENABLED:
        logger.info("Experiment queue worker disabled")
        return

    worker_stop_event.clear()
    worker_task = asyncio.create_task(run_experiment_queue_worker(worker_stop_event))


@app.on_event("shutdown")
async def shutdown_experiment_queue_worker() -> None:
    global worker_task

    if worker_task is None:
        return

    worker_stop_event.set()
    await worker_task
    worker_task = None