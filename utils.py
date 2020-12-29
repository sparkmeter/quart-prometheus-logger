from datetime import datetime, time, timezone


def now_utc() -> datetime:
    """Get a timezone-aware representation of now()."""
    return datetime.now(timezone.utc)
