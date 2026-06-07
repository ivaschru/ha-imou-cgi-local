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
    # Kept as ``digital_input`` for entity-registry compatibility with releases
    # before 0.2.2.  The value now means "doorbell/button event is active" and
    # can be driven by DB61i ``AlarmLocal`` or by legacy ``DigitalInput`` codes.
    digital_input: bool = False
    motion: bool = False
    event_count: int = 0
    # Counts only real doorbell/button press starts.  A binary sensor can stay
    # ``on`` between AlarmLocal Start/Stop events, so this counter gives Home
    # Assistant automations an event-like source that still fires for repeated
    # presses during one active window.
    doorbell_event_count: int = 0
    last_event: CgiEvent | None = None
    last_doorbell_event: CgiEvent | None = None
    last_error: str | None = None
    last_connected_at: datetime | None = None
    last_disconnected_at: datetime | None = None
    last_reconnect_at: datetime | None = None
    last_reconnect_reason: str | None = None
    reconnect_count: int = 0
    consecutive_failures: int = 0
    wdr_enabled: bool | None = None
    extra: dict[str, Any] = field(default_factory=dict)
