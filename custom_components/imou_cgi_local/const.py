"""Constants for the local Imou/Dahua CGI integration."""

from __future__ import annotations

from homeassistant.const import Platform


DOMAIN = "imou_cgi_local"

CONF_EVENT_CODES = "event_codes"
CONF_DIGITAL_INPUT_TIMEOUT = "digital_input_timeout"
CONF_MOTION_TIMEOUT = "motion_timeout"
CONF_RECONNECT_DELAY = "reconnect_delay"

DEFAULT_NAME = "Imou CGI Local"
DEFAULT_PORT = 80

# DB61i exposes Dahua-style event names.  ``VideoMotion`` is the useful binary
# motion event. ``VideoMotionInfo`` is included because the camera sends state
# heartbeats for it and those heartbeats prove that the CGI event stream itself
# is still alive.
#
# A physical DB61i button press was observed as ``AlarmLocal`` Start/Stop on the
# CGI stream, while the older assumed ``DigitalInput`` code did not fire on that
# device.  Keep ``DigitalInput`` subscribed for Dahua/Imou models where it really
# is the button input, but treat ``AlarmLocal`` as the primary DB61i doorbell
# event.
DEFAULT_EVENT_CODES = ["VideoMotion", "VideoMotionInfo", "DigitalInput", "AlarmLocal"]
DOORBELL_EVENT_CODES = {"DigitalInput", "AlarmLocal"}

# The camera sometimes sends ``Start`` without a matching ``Stop`` when the
# connection is interrupted.  Keep motion active long enough for a Telegram
# recording automation to catch it, then clear it defensively.
DEFAULT_DIGITAL_INPUT_TIMEOUT = 10
DEFAULT_MOTION_TIMEOUT = 75
DEFAULT_RECONNECT_DELAY = 5

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR, Platform.SWITCH]

WDR_CONFIG_KEY = "VideoInOptions[0].WideDynamicRange"
