# Changelog

## 0.1.0-preview — 2026-10-25

Initial public preview of an independent SideTap derivative.

### Added

- Local panel-action recorder and versioned JSON workflows.
- Explicit input parameters instead of saved typed values.
- Foreground-app, lock-state and point-dimension checks before replay steps.
- Unique text/type element resolution for recorded taps and long presses.
- Optional post-action visible-text assertions.
- Per-step results, available screenshots, local JSON reports, and cancellation.
- Compact Chinese workflow workbench and `launch.py --flows` entry point.
- 37 workflow logic and HTTP integration tests, bilingual README and setup/format/limitation documentation.

### Inherited and adapted

- SideTap's Windows/USB control, diagnostics, viewer, Agent/MCP helpers and tests.
- Chinese interface adjustments, loopback-only USB forwarding, and Windows process-output handling.

### Validation and limitations

- Recorder/replay verified with simulated devices and a browser workflow.
- Clean publication snapshot: 595 tests passed on Windows / Python 3.12.14.
- The new workflow feature has not yet been verified end-to-end on a real iPhone.
- Direct phone touches and other Agent processes are not recorded.
- JSON editing is the current flow editor. There is no no-code visual step editor.
- A transport/app check passing does not prove a business operation succeeded.

See `docs/VALIDATION.md` for exact test evidence.
