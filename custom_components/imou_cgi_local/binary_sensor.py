"""Binary sensors for the local Imou/Dahua CGI integration."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
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
    """Set up motion and stream-health binary sensors."""

    runtime: ImouCgiRuntime = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            ImouCgiMotionSensor(runtime, entry.entry_id),
            ImouCgiDoorbellSensor(runtime, entry.entry_id),
            ImouCgiConnectedSensor(runtime, entry.entry_id),
        ]
    )


class ImouCgiMotionSensor(ImouCgiEntity, BinarySensorEntity):
    """Binary motion sensor driven by CGI ``VideoMotion`` events."""

    _attr_name = "CGI motion"
    _attr_device_class = BinarySensorDeviceClass.MOTION

    def __init__(self, runtime: ImouCgiRuntime, entry_id: str) -> None:
        super().__init__(runtime, entry_id)
        self._attr_unique_id = f"{entry_id}_cgi_motion"

    @property
    def is_on(self) -> bool:
        """Return true while the latest CGI event says motion is active."""

        return bool(self.runtime.data.motion)


class ImouCgiConnectedSensor(ImouCgiEntity, BinarySensorEntity):
    """Connectivity sensor for the long-lived CGI event stream."""

    _attr_name = "CGI event stream connected"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, runtime: ImouCgiRuntime, entry_id: str) -> None:
        super().__init__(runtime, entry_id)
        self._attr_unique_id = f"{entry_id}_cgi_event_stream_connected"

    @property
    def is_on(self) -> bool:
        """Return true while the CGI event subscription is healthy."""

        return bool(self.runtime.data.connected)

    @property
    def extra_state_attributes(self) -> dict[str, str | int | None]:
        """Expose stream health and reconnect diagnostics."""

        data = self.runtime.data
        return {
            "last_connected_at": data.last_connected_at.isoformat()
            if data.last_connected_at
            else None,
            "last_disconnected_at": data.last_disconnected_at.isoformat()
            if data.last_disconnected_at
            else None,
            "last_reconnect_at": data.last_reconnect_at.isoformat()
            if data.last_reconnect_at
            else None,
            "last_reconnect_reason": data.last_reconnect_reason,
            "reconnect_count": data.reconnect_count,
            "consecutive_failures": data.consecutive_failures,
            "last_error": data.last_error,
        }


class ImouCgiDoorbellSensor(ImouCgiEntity, BinarySensorEntity):
    """Momentary doorbell sensor driven by CGI button-related events."""

    _attr_name = "CGI doorbell"

    def __init__(self, runtime: ImouCgiRuntime, entry_id: str) -> None:
        super().__init__(runtime, entry_id)
        # Preserve the original unique id so existing installations keep the
        # same entity registry row and helper references after the semantic fix.
        self._attr_unique_id = f"{entry_id}_cgi_digital_input"

    @property
    def is_on(self) -> bool:
        """Return true while a CGI doorbell event is active."""

        return bool(self.runtime.data.digital_input)
