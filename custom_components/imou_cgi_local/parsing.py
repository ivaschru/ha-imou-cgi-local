"""Pure parsing helpers for Dahua/Imou CGI event streams."""

from __future__ import annotations

from datetime import datetime, timezone

from .models import CgiEvent


def _utcnow() -> datetime:
    """Return a timezone-aware UTC timestamp for parsed events."""

    return datetime.now(timezone.utc)


def parse_event_line(line: str) -> CgiEvent | None:
    """Parse one ``Code=...;action=...`` event line.

    Dahua multipart responses include boundary and header lines as well as JSON
    payload lines.  Only the compact ``Code=`` line changes entity state; every
    other line is ignored.
    """

    if not line.startswith("Code="):
        return None

    parts: dict[str, str] = {}
    for item in line.split(";"):
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        parts[key.strip()] = value.strip()

    code = parts.get("Code")
    action = parts.get("action")
    if not code or not action:
        return None

    return CgiEvent(
        code=code,
        action=action,
        index=parts.get("index"),
        raw=line,
        received_at=_utcnow(),
    )
