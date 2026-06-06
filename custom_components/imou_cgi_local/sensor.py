"""Diagnostic sensors for the local Imou/Dahua CGI integration."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ImouCgiRuntime
from .entity import ImouCgiEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up last-event and event-count diagnostic sensors."""

    runtime: ImouCgiRuntime = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            ImouCgiLastEventSensor(runtime, entry.entry_id),
            ImouCgiEventCountSensor(runtime, entry.entry_id),
        ]
    )


class ImouCgiLastEventSensor(ImouCgiEntity, SensorEntity):
    """Expose the most recent parsed CGI event."""

    _attr_name = "CGI last event"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, runtime: ImouCgiRuntime, entry_id: str) -> None:
        super().__init__(runtime, entry_id)
        self._attr_unique_id = f"{entry_id}_cgi_last_event"

    @property
    def native_value(self) -> str:
        """Return a compact event name suitable for the state column."""

        event = self.runtime.data.last_event
        if event is None:
            return "none"
        return f"{event.code} {event.action}"[:255]

    @property
    def extra_state_attributes(self) -> dict[str, str | int | None]:
        """Expose parsed and raw event details for troubleshooting."""

        data = self.runtime.data
        event = data.last_event
        if event is None:
            return {
                "event_count": data.event_count,
                "last_error": data.last_error,
            }
        return {
            "code": event.code,
            "action": event.action,
            "index": event.index,
            "raw": event.raw,
            "received_at": event.received_at.isoformat(),
            "event_count": data.event_count,
            "last_error": data.last_error,
        }


class ImouCgiEventCountSensor(ImouCgiEntity, SensorEntity):
    """Count parsed CGI event lines since integration setup."""

    _attr_name = "CGI event count"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, runtime: ImouCgiRuntime, entry_id: str) -> None:
        super().__init__(runtime, entry_id)
        self._attr_unique_id = f"{entry_id}_cgi_event_count"

    @property
    def native_value(self) -> int:
        """Return the number of parsed ``Code=`` event lines."""

        return self.runtime.data.event_count
