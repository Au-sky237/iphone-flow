# Contributing

Small, reproducible improvements are welcome. Read `NOTICE.md` for the source
lineage and preserve attribution when changing inherited code.

## Local checks

Use Python 3.12 on Windows. Install `requirements.txt` and `pytest`, then run:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
python -m pytest tests -q
```

Tests use simulated devices and local HTTP servers. They must not require or
operate a real phone. New failure handling should be tested for missing
elements, timeouts, input redaction, and cancellation where applicable.

## Useful contributions

- Reproducible real-device validation: device model, iOS version, WDA/go-ios
  versions, exact steps, expected result, and observed result.
- Cleaner setup instructions based on an independently tested Windows machine.
- Element selection failures with synthetic or carefully redacted examples.
- Documentation corrections and UI translations.

Do not attach a real `.env`, Apple credentials, signing material, device IDs,
personal screenshots, or private recordings to a public issue. Use synthetic
data. If a change affects a phone action, state how it was verified; do not
describe a simulator result as a real-device pass.

Keep pull requests focused. Workflows are data, not executable code. A timeout
must never trigger an automatic replay of the action that timed out.
