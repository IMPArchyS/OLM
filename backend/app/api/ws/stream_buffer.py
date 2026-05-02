from threading import Lock
from typing import Any

from app.core.config import settings


# threading.Lock (not asyncio.Lock) is intentional — _read_stream_samples is called
# from a sync FastAPI route handler, making asyncio.Lock incompatible here.
_stream_buffer_lock = Lock()
_stream_buffers: dict[int, list[dict[str, Any]]] = {}


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
