import asyncio
import logging
from datetime import datetime, time, timedelta

from sqlmodel import Session, select

from app.api.dependencies import engine
from app.api.endpoints.server import finish_server_sync, ping_remote_server, resolve_url, try_start_server_sync
from app.core.config import settings
from app.models.server import Server, ServerPublic
from app.models.utils import ensure

logger = logging.getLogger("uvicorn.error")


def _run_sync_tick() -> None:
    with Session(engine) as db:
        servers = db.exec(select(Server)).all()
        for db_server in servers:
            if not try_start_server_sync(ensure(db_server.id)):
                logger.info("WORKER: sync skipped server_id=%s reason=sync_in_progress", db_server.id)
                continue
            try:
                health_url = resolve_url(db_server)
                if not health_url:
                    continue
                health_url += settings.EXPERIMENTAL_HEALTH_PATH
                db_server.available = ping_remote_server(db, ServerPublic.model_validate(db_server), health_url)
                db.add(db_server)
                db.commit()
                logger.info("WORKER: sync done server_id=%s available=%s", db_server.id, db_server.available)
            except Exception:
                logger.exception("WORKER: sync failed server_id=%s", db_server.id)
            finally:
                finish_server_sync(ensure(db_server.id))


def _seconds_until_next(target: time) -> float:
    now = datetime.now()
    next_run = datetime.combine(now.date(), target)
    if next_run <= now:
        next_run += timedelta(days=1)
    return (next_run - now).total_seconds()


async def run_sync_worker(stop_event: asyncio.Event) -> None:
    logger.info("WORKER: sync worker started")

    try:
        await asyncio.to_thread(_run_sync_tick)
    except Exception:
        logger.exception("WORKER: sync startup tick failed")

    while not stop_event.is_set():
        delay = _seconds_until_next(settings.SERVER_SYNC_WORKER_TIME)
        logger.info("WORKER: sync next run in %.0fs", delay)
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=delay)
        except asyncio.TimeoutError:
            pass

        if stop_event.is_set():
            break

        try:
            await asyncio.to_thread(_run_sync_tick)
        except Exception:
            logger.exception("WORKER: sync tick failed")

    logger.info("WORKER: sync worker stopped")
