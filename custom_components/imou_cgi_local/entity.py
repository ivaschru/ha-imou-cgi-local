"""Base entity helpers for the local Imou/Dahua CGI integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ImouCgiRuntime


class ImouCgiEntity(CoordinatorEntity):
    """Base entity bound to one CGI runtime coordinator."""

    _attr_has_entity_name = True

    def __init__(self, runtime: ImouCgiRuntime, entry_id: str) -> None:
        super().__init__(runtime.coordinator)
        self.runtime = runtime
        self._entry_id = entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=runtime.name,
            manufacturer="Imou/Dahua",
            model="Local CGI camera",
            configuration_url=runtime.client.credentials.base_url,
        )
