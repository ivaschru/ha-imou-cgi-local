# AGENTS.md

## Project Purpose

- This repository is a HACS-compatible Home Assistant custom integration.
- The integration reads local Imou/Dahua CGI event streams and exposes them as
  Home Assistant entities.
- Do not commit real camera credentials, Home Assistant tokens, logs containing
  secrets, or private Home Assistant storage files.

## Structure

- `custom_components/imou_cgi_local/` — Home Assistant integration source.
- `hacs.json` — HACS metadata.
- `tests/` — parser/unit tests that do not require Home Assistant runtime.

## Development Rules

- Keep runtime dependencies empty unless there is a strong reason to add one.
  The integration currently uses Python stdlib Digest auth and Home Assistant
  APIs only.
- Blocking camera I/O must stay outside the Home Assistant event loop. Use
  executor jobs for short CGI reads and the existing background worker for the
  long-lived event stream.
- Keep comments explicit around the CGI stream parser and threading boundary;
  that code is easy to break with seemingly harmless refactors.
- Update `README.md` when entity behavior, setup fields, or supported CGI
  endpoints change.
