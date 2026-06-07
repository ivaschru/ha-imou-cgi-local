"""Tests for Dahua/Imou CGI event parsing."""

from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "imou_cgi_local"

package = types.ModuleType("imou_cgi_local")
package.__path__ = [str(COMPONENT)]
sys.modules["imou_cgi_local"] = package

for module_name in ["models", "parsing"]:
    spec = importlib.util.spec_from_file_location(
        f"imou_cgi_local.{module_name}",
        COMPONENT / f"{module_name}.py",
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"imou_cgi_local.{module_name}"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)

from imou_cgi_local.parsing import parse_event_line  # noqa: E402


class EventParsingTest(unittest.TestCase):
    def test_video_motion_start(self) -> None:
        event = parse_event_line("Code=VideoMotion;action=Start;index=0;data={")

        self.assertIsNotNone(event)
        self.assertEqual(event.code, "VideoMotion")
        self.assertEqual(event.action, "Start")
        self.assertEqual(event.index, "0")

    def test_video_motion_stop(self) -> None:
        event = parse_event_line("Code=VideoMotion;action=Stop;index=0")

        self.assertIsNotNone(event)
        self.assertEqual(event.code, "VideoMotion")
        self.assertEqual(event.action, "Stop")
        self.assertEqual(event.index, "0")

    def test_digital_input_start(self) -> None:
        event = parse_event_line("Code=DigitalInput;action=Start;index=0")

        self.assertIsNotNone(event)
        self.assertEqual(event.code, "DigitalInput")
        self.assertEqual(event.action, "Start")
        self.assertEqual(event.index, "0")

    def test_alarm_local_start(self) -> None:
        event = parse_event_line("Code=AlarmLocal;action=Start;index=0")

        self.assertIsNotNone(event)
        self.assertEqual(event.code, "AlarmLocal")
        self.assertEqual(event.action, "Start")
        self.assertEqual(event.index, "0")

    def test_ignores_multipart_headers(self) -> None:
        self.assertIsNone(parse_event_line("--myboundary"))
        self.assertIsNone(parse_event_line("Content-Type: text/plain"))
        self.assertIsNone(parse_event_line('"RegionName" : [ "Region1" ]'))


if __name__ == "__main__":
    unittest.main()
