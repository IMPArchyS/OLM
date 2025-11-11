from datetime import datetime, timezone


def now() -> datetime:
    """Return the current time as an aware UTC datetime."""
    return datetime.now(timezone.utc)