"""Blocking local CGI client for Imou/Dahua devices.

Home Assistant's event loop must never wait on the camera.  This module is
therefore deliberately blocking and is used only from executor jobs or from the
dedicated event-stream worker thread.
"""

from __future__ import annotations

import socket
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

from .const import WDR_CONFIG_KEY


class ImouCgiError(RuntimeError):
    """Raised when the camera CGI endpoint cannot be read or parsed."""


@dataclass(frozen=True)
class ImouCgiCredentials:
    """Connection data for one local camera web service."""

    host: str
    port: int
    username: str
    password: str

    @property
    def base_url(self) -> str:
        """Return the camera HTTP base URL without embedding credentials."""

        return f"http://{self.host}:{self.port}"


class ImouCgiClient:
    """Small Digest-auth client for Dahua-style CGI endpoints."""

    def __init__(self, credentials: ImouCgiCredentials) -> None:
        self.credentials = credentials

    def _build_opener(self) -> urllib.request.OpenerDirector:
        """Create a fresh Digest opener.

        ``urllib`` stores nonce/cnonce state on the opener.  A fresh opener per
        request avoids cross-thread state sharing between the event worker and
        Home Assistant service/entity calls.
        """

        manager = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        manager.add_password(
            None,
            f"{self.credentials.base_url}/",
            self.credentials.username,
            self.credentials.password,
        )
        return urllib.request.build_opener(urllib.request.HTTPDigestAuthHandler(manager))

    def request_text(self, path: str, *, timeout: float = 10.0) -> tuple[int, str]:
        """Return ``(HTTP status, body text)`` for one CGI request."""

        opener = self._build_opener()
        request = urllib.request.Request(
            f"{self.credentials.base_url}{path}",
            headers={"User-Agent": "home-assistant-imou-cgi-local/0.1"},
        )
        try:
            with opener.open(request, timeout=timeout) as response:
                return response.status, response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            return exc.code, body
        except (OSError, TimeoutError, socket.timeout) as exc:
            raise ImouCgiError(f"CGI request failed: {exc}") from exc

    def get_config(self, name: str) -> str:
        """Read one Dahua-style configuration namespace."""

        query = urllib.parse.urlencode({"action": "getConfig", "name": name})
        status, body = self.request_text(f"/cgi-bin/configManager.cgi?{query}")
        if status != 200:
            raise ImouCgiError(f"getConfig {name} returned HTTP {status}: {body[:200]}")
        if body.startswith("Error"):
            raise ImouCgiError(f"getConfig {name} returned {body.strip()}")
        return body

    def set_config_value(self, key: str, value: str) -> None:
        """Set one Dahua-style configuration value."""

        # Brackets in the CGI key are intentionally URL-encoded; DB61i accepts
        # both encoded and plain forms, and encoded form is safer for generic
        # HTTP clients.
        query = urllib.parse.urlencode({"action": "setConfig", key: value})
        status, body = self.request_text(f"/cgi-bin/configManager.cgi?{query}")
        if status != 200 or body.strip() != "OK":
            raise ImouCgiError(f"setConfig {key} returned HTTP {status}: {body[:200]}")

    def get_wdr_enabled(self) -> bool:
        """Return whether Wide Dynamic Range/HDR is enabled."""

        config = self.get_config("VideoInOptions")
        prefix = f"table.{WDR_CONFIG_KEY}="
        for line in config.splitlines():
            if line.startswith(prefix):
                value = line.rsplit("=", 1)[1].strip()
                return value in {"1", "true", "True"}
        raise ImouCgiError(f"{WDR_CONFIG_KEY} is missing in VideoInOptions")

    def set_wdr_enabled(self, enabled: bool) -> None:
        """Enable or disable Wide Dynamic Range/HDR."""

        self.set_config_value(WDR_CONFIG_KEY, "1" if enabled else "0")

    def validate(self) -> None:
        """Validate credentials against a read-only endpoint."""

        motion_config = self.get_config("MotionDetect")
        if "MotionDetect" not in motion_config:
            raise ImouCgiError("MotionDetect config was readable but unexpected.")

    def open_event_stream(self, event_codes: list[str], *, timeout: float = 10.0):
        """Open the long-lived CGI event stream.

        The caller owns and closes the returned response object.  The URL is
        equivalent to:
        ``/cgi-bin/eventManager.cgi?action=attach&codes=[VideoMotion,...]``.
        """

        codes = "[" + ",".join(event_codes) + "]"
        query = urllib.parse.urlencode({"action": "attach", "codes": codes})
        opener = self._build_opener()
        request = urllib.request.Request(
            f"{self.credentials.base_url}/cgi-bin/eventManager.cgi?{query}",
            headers={"User-Agent": "home-assistant-imou-cgi-local/0.1"},
        )
        return opener.open(request, timeout=timeout)
