"""Runtime coordinator and CGI event-stream worker."""

from __future__ import annotations

import logging
import socket
import threading
import time
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import ImouCgiClient
from .models import CgiEvent, CgiRuntimeData
from .parsing import parse_event_line

_LOGGER = logging.getLogger(__name__)


def _utcnow() -> datetime:
    """Return a timezone-aware UTC timestamp for entity attributes."""

    return datetime.now(timezone.utc)


class ImouCgiRuntime:
    """Owns the camera client, coordinator and background event worker."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: ImouCgiClient,
        *,
        name: str,
        event_codes: list[str],
        motion_timeout: int,
        reconnect_delay: int,
    ) -> None:
        self.hass = hass
        self.client = client
        self.name = name
        self.event_codes = event_codes
        self.motion_timeout = motion_timeout
        self.reconnect_delay = reconnect_delay
        self.coordinator: DataUpdateCoordinator[CgiRuntimeData] = DataUpdateCoordinator(
            hass,
            _LOGGER,
            name=f"{name} CGI",
        )
        self.coordinator.async_set_updated_data(CgiRuntimeData())
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._event_count = 0
        self._motion = False
        self._last_video_motion_at: datetime | None = None

    @property
    def data(self) -> CgiRuntimeData:
        """Return the latest immutable data snapshot."""

        return self.coordinator.data or CgiRuntimeData()

    async def async_start(self) -> None:
        """Read initial static state and start the event stream."""

        await self.async_refresh_wdr()
        self._thread = threading.Thread(
            target=self._run_event_stream_forever,
            name=f"imou-cgi-local-{self.name}",
            daemon=True,
        )
        self._thread.start()

    async def async_stop(self) -> None:
        """Stop the event worker during config entry unload."""

        self._stop_event.set()
        thread = self._thread
        if thread is not None:
            await self.hass.async_add_executor_job(thread.join, 5)

    async def async_refresh_wdr(self) -> None:
        """Refresh the WDR/HDR switch state from the camera."""

        try:
            enabled = await self.hass.async_add_executor_job(self.client.get_wdr_enabled)
        except Exception as exc:  # noqa: BLE001 - surfaced as diagnostic state.
            self._publish(last_error=f"WDR read failed: {exc}")
            return
        self._publish(wdr_enabled=enabled, last_error=None)

    async def async_set_wdr(self, enabled: bool) -> None:
        """Set WDR/HDR through CGI and refresh the switch state."""

        await self.hass.async_add_executor_job(self.client.set_wdr_enabled, enabled)
        await self.async_refresh_wdr()

    def _thread_publish(self, **changes: Any) -> None:
        """Publish worker-thread changes on Home Assistant's event loop."""

        self.hass.loop.call_soon_threadsafe(self._publish, **changes)

    def _publish(self, **changes: Any) -> None:
        """Create a new immutable snapshot and notify all entities."""

        current = self.data
        next_data = replace(current, **changes)
        self.coordinator.async_set_updated_data(next_data)

    def _set_connected(self, connected: bool, *, error: str | None = None) -> None:
        """Update connection diagnostics from the worker thread."""

        now = _utcnow()
        if connected:
            self._thread_publish(
                connected=True,
                last_error=None,
                last_connected_at=now,
            )
        else:
            self._thread_publish(
                connected=False,
                last_error=error,
                last_disconnected_at=now,
            )

    def _handle_event(self, event: CgiEvent) -> None:
        """Apply one parsed camera event to the coordinator data."""

        # DB61i emits ``VideoMotion`` Start/Stop events for motion detection.
        # ``VideoMotionInfo`` State events are useful as stream heartbeats but
        # should not toggle the binary motion sensor by themselves.
        if event.code == "VideoMotion" and event.action.lower() == "start":
            self._motion = True
            self._last_video_motion_at = event.received_at
        elif event.code == "VideoMotion" and event.action.lower() == "stop":
            self._motion = False
            self._last_video_motion_at = event.received_at

        self._event_count += 1

        self._thread_publish(
            motion=self._motion,
            event_count=self._event_count,
            last_event=event,
            last_error=None,
        )

    def _expire_motion_if_needed(self) -> None:
        """Clear motion if a Start event was not followed by Stop."""

        if not self._motion or self._last_video_motion_at is None:
            return
        elapsed = (_utcnow() - self._last_video_motion_at).total_seconds()
        if elapsed >= self.motion_timeout:
            self._motion = False
            self._thread_publish(motion=False)

    def _run_event_stream_forever(self) -> None:
        """Keep a persistent Digest-auth CGI event subscription alive."""

        while not self._stop_event.is_set():
            try:
                with self.client.open_event_stream(
                    self.event_codes,
                    timeout=max(30, self.motion_timeout),
                ) as response:
                    self._set_connected(True)
                    self._read_event_stream(response)
            except Exception as exc:  # noqa: BLE001 - diagnostics must survive bad cameras.
                _LOGGER.debug("Imou CGI event stream failed", exc_info=True)
                self._set_connected(False, error=str(exc))

            self._expire_motion_if_needed()
            self._stop_event.wait(self.reconnect_delay)

    def _read_event_stream(self, response: Any) -> None:
        """Read multipart text stream until stopped or a read failure occurs."""

        line = bytearray()
        while not self._stop_event.is_set():
            try:
                chunk = response.read(1)
            except (OSError, TimeoutError, socket.timeout) as exc:
                # ``urllib`` turns idle long-poll reads into timeout objects.
                # Reconnecting is cheap and also acts as a stream watchdog.
                raise RuntimeError(f"event stream read timeout: {exc}") from exc

            if not chunk:
                raise RuntimeError("event stream closed by camera")

            line.extend(chunk)
            if chunk not in {b"\n", b"\r"} and len(line) < 2048:
                continue

            text = line.decode("utf-8", errors="replace").strip()
            line.clear()
            if not text:
                self._expire_motion_if_needed()
                continue

            event = parse_event_line(text)
            if event is not None:
                self._handle_event(event)
            self._expire_motion_if_needed()
