"""Switches for the local Imou/Dahua CGI integration."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ImouCgiRuntime
from .entity import ImouCgiEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up CGI-controlled camera switches."""

    runtime: ImouCgiRuntime = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ImouCgiWdrSwitch(runtime, entry.entry_id)])


class ImouCgiWdrSwitch(ImouCgiEntity, SwitchEntity):
    """Wide Dynamic Range/HDR switch backed by ``VideoInOptions`` CGI config."""

    _attr_name = "CGI HDR"

    def __init__(self, runtime: ImouCgiRuntime, entry_id: str) -> None:
        super().__init__(runtime, entry_id)
        self._attr_unique_id = f"{entry_id}_cgi_wdr"

    @property
    def is_on(self) -> bool | None:
        """Return the latest known HDR/WDR state."""

        return self.runtime.data.wdr_enabled

    async def async_turn_on(self, **kwargs) -> None:
        """Enable HDR/WDR through local CGI."""

        await self.runtime.async_set_wdr(True)

    async def async_turn_off(self, **kwargs) -> None:
        """Disable HDR/WDR through local CGI."""

        await self.runtime.async_set_wdr(False)

    async def async_update(self) -> None:
        """Refresh HDR/WDR state when Home Assistant polls this entity."""

        await self.runtime.async_refresh_wdr()
