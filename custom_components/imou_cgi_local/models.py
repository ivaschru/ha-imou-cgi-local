"""Shared data models for the local Imou/Dahua CGI integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class CgiEvent:
    """One parsed Dahua/Imou CGI event line.

    The event stream is a multipart text stream where the useful line usually
    looks like ``Code=VideoMotion;action=Start;index=0``.  Payload lines after
    ``data={`` are intentionally not required for the motion sensor, but the raw
    first line is preserved for diagnostics.
    """

    code: str
    action: str
    index: str | None
    raw: str
    received_at: datetime


@dataclass(frozen=True)
class CgiRuntimeData:
    """Immutable snapshot consumed by Home Assistant entities."""

    connected: bool = False
    motion: bool = False
    event_count: int = 0
    last_event: CgiEvent | None = None
    last_error: str | None = None
    last_connected_at: datetime | None = None
    last_disconnected_at: datetime | None = None
    wdr_enabled: bool | None = None
    extra: dict[str, Any] = field(default_factory=dict)
