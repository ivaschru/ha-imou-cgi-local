# Imou CGI Local for Home Assistant

Home Assistant custom integration for reading local Dahua/Imou CGI events from
Imou cameras and doorbells.

The integration is intended for HACS installation. It talks directly to the
camera over the local HTTP web service and does not use the Imou cloud.

## Why this exists

Some Imou/Dahua devices expose motion events through the local CGI endpoint:

```text
/cgi-bin/eventManager.cgi?action=attach&codes=[VideoMotion,VideoMotionInfo]
```

On at least one `IMOU DB61i` doorbell, this CGI event stream kept reporting
`VideoMotion` events while Home Assistant's standard ONVIF event subscription
stopped updating its motion binary sensors. This integration gives Home
Assistant an independent local motion source for that case.

## Features

- Add one or more local cameras through the Home Assistant UI.
- Authenticate to the camera web service with HTTP Digest authentication.
- Subscribe to the long-lived local CGI event stream.
- Expose a motion binary sensor from `VideoMotion` `Start` / `Stop` events.
- Expose an event-stream connectivity binary sensor.
- Expose diagnostic sensors for the last parsed event and event count.
- Expose a Wide Dynamic Range / HDR switch backed by
  `VideoInOptions[0].WideDynamicRange`.
- Reconnect automatically if the event stream times out or the camera closes
  the connection.

## Entities

Each configured camera creates these entities:

- `CGI motion`
- `CGI event stream connected`
- `CGI last event`
- `CGI event count`
- `CGI HDR`

## Installation with HACS

1. Open HACS in Home Assistant.
2. Open custom repositories.
3. Add this repository URL as category `Integration`:
   `https://github.com/ivaschru/ha-imou-cgi-local`
4. Install `Imou CGI Local`.
5. Restart Home Assistant.
6. Go to **Settings -> Devices & services -> Add integration**.
7. Search for `Imou CGI Local`.
8. Enter the camera host, HTTP port, username and password.

## Manual Installation

Copy `custom_components/imou_cgi_local` into your Home Assistant
`custom_components` directory, then restart Home Assistant.

## Configuration

The setup form accepts:

- `Host`: camera IP address or hostname.
- `HTTP port`: usually `80`.
- `Username` / `Password`: local camera web/ONVIF credentials.
- `Event codes`: comma-separated Dahua/Imou event codes. Defaults to
  `VideoMotion,VideoMotionInfo`.
- `Motion timeout`: fallback time in seconds before clearing motion if a
  `Start` event is not followed by `Stop`.
- `Reconnect delay`: delay in seconds before reopening the event stream after a
  read timeout or disconnect.

## Notes

- This integration does not replace the camera stream in the first release.
  Keep using ONVIF, Generic Camera, go2rtc, WebRTC or another known-good stream
  source for video.
- The integration deliberately uses the CGI event stream for motion because it
  can continue working when ONVIF event subscription state in Home Assistant is
  stale.
- The password is stored by Home Assistant in config entry storage, not in YAML.
- The CGI API is a Dahua/Imou local device API. It is useful and widely known,
  but it is not a formal Home Assistant integration contract.

## Troubleshooting

If setup fails:

- Check that Home Assistant can reach the camera over plain HTTP.
- Open `http://<camera-ip>/` from the same network and confirm that the web
  service responds.
- Confirm that the same username and password work for a Digest-auth CGI
  request such as:

```bash
curl --digest -u 'USER:PASS' \
  'http://CAMERA_IP/cgi-bin/configManager.cgi?action=getConfig&name=MotionDetect'
```

If events do not appear:

- Enable debug logging:

```yaml
logger:
  logs:
    custom_components.imou_cgi_local: debug
```

- Check `CGI event stream connected`.
- Check `CGI last event` and `CGI event count`.
- Test the camera directly:

```bash
curl --digest -u 'USER:PASS' --globoff -N \
  'http://CAMERA_IP/cgi-bin/eventManager.cgi?action=attach&codes=[VideoMotion,VideoMotionInfo]'
```
