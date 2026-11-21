import html
from datetime import datetime, timezone


def esc(val: object) -> str:
    """Escape a value safely for Telegram HTML parse mode."""
    return html.escape(str(val if val is not None else ""), quote=False)


def utcnow() -> datetime:
    """Return naive UTC datetime compatible with existing SQLite columns without deprecation warnings."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
