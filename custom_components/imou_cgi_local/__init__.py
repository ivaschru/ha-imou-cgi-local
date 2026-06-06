"""Home Assistant setup for the local Imou/Dahua CGI integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .api import ImouCgiClient, ImouCgiCredentials
from .const import (
    CONF_EVENT_CODES,
    CONF_DIGITAL_INPUT_TIMEOUT,
    CONF_MOTION_TIMEOUT,
    CONF_RECONNECT_DELAY,
    DEFAULT_DIGITAL_INPUT_TIMEOUT,
    DEFAULT_EVENT_CODES,
    DEFAULT_MOTION_TIMEOUT,
    DEFAULT_RECONNECT_DELAY,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import ImouCgiRuntime


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up one local CGI camera config entry."""

    data = entry.data
    options = entry.options

    credentials = ImouCgiCredentials(
        host=data[CONF_HOST],
        port=int(data.get(CONF_PORT, 80)),
        username=data[CONF_USERNAME],
        password=data[CONF_PASSWORD],
    )
    runtime = ImouCgiRuntime(
        hass,
        ImouCgiClient(credentials),
        name=data.get(CONF_NAME, entry.title),
        event_codes=list(options.get(CONF_EVENT_CODES, DEFAULT_EVENT_CODES)),
        digital_input_timeout=int(
            options.get(CONF_DIGITAL_INPUT_TIMEOUT, DEFAULT_DIGITAL_INPUT_TIMEOUT)
        ),
        motion_timeout=int(options.get(CONF_MOTION_TIMEOUT, DEFAULT_MOTION_TIMEOUT)),
        reconnect_delay=int(options.get(CONF_RECONNECT_DELAY, DEFAULT_RECONNECT_DELAY)),
    )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = runtime
    await runtime.async_start()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload one local CGI camera config entry."""

    runtime: ImouCgiRuntime | None = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if runtime is not None:
        await runtime.async_stop()
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
