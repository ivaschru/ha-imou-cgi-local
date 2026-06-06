"""Config flow for the local Imou/Dahua CGI integration."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .api import ImouCgiClient, ImouCgiCredentials, ImouCgiError
from .const import (
    CONF_EVENT_CODES,
    CONF_DIGITAL_INPUT_TIMEOUT,
    CONF_MOTION_TIMEOUT,
    CONF_RECONNECT_DELAY,
    DEFAULT_DIGITAL_INPUT_TIMEOUT,
    DEFAULT_EVENT_CODES,
    DEFAULT_MOTION_TIMEOUT,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_RECONNECT_DELAY,
    DOMAIN,
)


def _event_codes_from_text(value: str | list[str]) -> list[str]:
    """Normalize comma-separated event codes from UI/API input."""

    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [item.strip() for item in str(value).split(",") if item.strip()]


def _event_codes_to_text(value: list[str]) -> str:
    """Render event codes as a compact UI string."""

    return ",".join(value)


async def _validate_input(hass: HomeAssistant, user_input: dict) -> None:
    """Validate CGI credentials without exposing them in errors."""

    credentials = ImouCgiCredentials(
        host=user_input[CONF_HOST],
        port=int(user_input[CONF_PORT]),
        username=user_input[CONF_USERNAME],
        password=user_input[CONF_PASSWORD],
    )
    client = ImouCgiClient(credentials)
    await hass.async_add_executor_job(client.validate)


class ImouCgiLocalConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Create a config entry for one local Imou/Dahua CGI camera."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial setup form."""

        errors: dict[str, str] = {}
        if user_input is not None:
            user_input = dict(user_input)
            user_input[CONF_PORT] = int(user_input.get(CONF_PORT, DEFAULT_PORT))
            try:
                await _validate_input(self.hass, user_input)
            except ImouCgiError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001 - Home Assistant maps this to an unknown setup error.
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(
                    f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
                )
                self._abort_if_unique_id_configured()
                options = {
                    CONF_EVENT_CODES: _event_codes_from_text(
                        user_input.pop(CONF_EVENT_CODES, DEFAULT_EVENT_CODES)
                    ),
                    CONF_DIGITAL_INPUT_TIMEOUT: int(
                        user_input.pop(
                            CONF_DIGITAL_INPUT_TIMEOUT,
                            DEFAULT_DIGITAL_INPUT_TIMEOUT,
                        )
                    ),
                    CONF_MOTION_TIMEOUT: int(
                        user_input.pop(CONF_MOTION_TIMEOUT, DEFAULT_MOTION_TIMEOUT)
                    ),
                    CONF_RECONNECT_DELAY: int(
                        user_input.pop(CONF_RECONNECT_DELAY, DEFAULT_RECONNECT_DELAY)
                    ),
                }
                return self.async_create_entry(
                    title=user_input.get(CONF_NAME, DEFAULT_NAME),
                    data=user_input,
                    options=options,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self._user_schema(user_input or {}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Return the options flow handler."""

        return ImouCgiLocalOptionsFlow(config_entry)

    def _user_schema(self, values: dict) -> vol.Schema:
        """Build the setup schema with stable defaults."""

        return vol.Schema(
            {
                vol.Required(CONF_NAME, default=values.get(CONF_NAME, DEFAULT_NAME)): str,
                vol.Required(CONF_HOST, default=values.get(CONF_HOST, "")): str,
                vol.Required(CONF_PORT, default=values.get(CONF_PORT, DEFAULT_PORT)): int,
                vol.Required(CONF_USERNAME, default=values.get(CONF_USERNAME, "")): str,
                vol.Required(
                    CONF_PASSWORD,
                    default=values.get(CONF_PASSWORD, ""),
                ): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                ),
                vol.Required(
                    CONF_EVENT_CODES,
                    default=values.get(
                        CONF_EVENT_CODES,
                        _event_codes_to_text(DEFAULT_EVENT_CODES),
                    ),
                ): str,
                vol.Required(
                    CONF_MOTION_TIMEOUT,
                    default=values.get(CONF_MOTION_TIMEOUT, DEFAULT_MOTION_TIMEOUT),
                ): int,
                vol.Required(
                    CONF_DIGITAL_INPUT_TIMEOUT,
                    default=values.get(
                        CONF_DIGITAL_INPUT_TIMEOUT,
                        DEFAULT_DIGITAL_INPUT_TIMEOUT,
                    ),
                ): int,
                vol.Required(
                    CONF_RECONNECT_DELAY,
                    default=values.get(CONF_RECONNECT_DELAY, DEFAULT_RECONNECT_DELAY),
                ): int,
            }
        )


class ImouCgiLocalOptionsFlow(config_entries.OptionsFlow):
    """Allow tuning event codes and watchdog timings after setup."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        """Show and save runtime options."""

        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={
                    CONF_EVENT_CODES: _event_codes_from_text(user_input[CONF_EVENT_CODES]),
                    CONF_DIGITAL_INPUT_TIMEOUT: int(user_input[CONF_DIGITAL_INPUT_TIMEOUT]),
                    CONF_MOTION_TIMEOUT: int(user_input[CONF_MOTION_TIMEOUT]),
                    CONF_RECONNECT_DELAY: int(user_input[CONF_RECONNECT_DELAY]),
                },
            )

        options = self.config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_EVENT_CODES,
                        default=_event_codes_to_text(
                            list(options.get(CONF_EVENT_CODES, DEFAULT_EVENT_CODES))
                        ),
                    ): str,
                    vol.Required(
                        CONF_MOTION_TIMEOUT,
                        default=int(options.get(CONF_MOTION_TIMEOUT, DEFAULT_MOTION_TIMEOUT)),
                    ): int,
                    vol.Required(
                        CONF_DIGITAL_INPUT_TIMEOUT,
                        default=int(
                            options.get(
                                CONF_DIGITAL_INPUT_TIMEOUT,
                                DEFAULT_DIGITAL_INPUT_TIMEOUT,
                            )
                        ),
                    ): int,
                    vol.Required(
                        CONF_RECONNECT_DELAY,
                        default=int(options.get(CONF_RECONNECT_DELAY, DEFAULT_RECONNECT_DELAY)),
                    ): int,
                }
            ),
        )
