from datetime import datetime, timezone


def now() -> datetime:
    """Return the current time as an aware UTC datetime."""
    return datetime.now(timezone.utc)


def ensure(value: int | None) -> int:
    """Check if the passed in Id field is not None."""
    if value is None: raise ValueError("Value is None")
    return value
