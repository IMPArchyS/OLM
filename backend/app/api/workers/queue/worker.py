import asyncio
import logging

import httpx

from app.core.config import settings
from .poll import run_poll_tick
from .submit import run_submit_tick

logger = logging.getLogger("uvicorn.error")


async def run_submit_worker(stop_event: asyncio.Event) -> None:
    logger.info("WORKER: submit worker started")
    async with httpx.AsyncClient(timeout=settings.EXPERIMENT_QUEUE_REQUEST_TIMEOUT_SECONDS) as client:
        while not stop_event.is_set():
            try:
                await run_submit_tick(client)
            except Exception:
                logger.exception("WORKER: submit tick failed")
            try:
                await asyncio.wait_for(
                    stop_event.wait(),
                    timeout=settings.EXPERIMENT_QUEUE_WORKER_INTERVAL_SECONDS,
                )
            except asyncio.TimeoutError:
                pass
    logger.info("WORKER: submit worker stopped")


async def run_poll_worker(stop_event: asyncio.Event) -> None:
    logger.info("WORKER: poll worker started")
    interval = 1.0 / settings.EXPERIMENT_QUEUE_POLL_RATE_PER_SECOND
    async with httpx.AsyncClient(timeout=settings.EXPERIMENT_QUEUE_REQUEST_TIMEOUT_SECONDS) as client:
        while not stop_event.is_set():
            try:
                await run_poll_tick(client)
            except Exception:
                logger.exception("WORKER: poll tick failed")
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=interval)
            except asyncio.TimeoutError:
                pass
    logger.info("WORKER: poll worker stopped")
