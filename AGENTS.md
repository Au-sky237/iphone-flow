# Project guidance

- This is a Windows-first derivative of SideTap. Preserve its MIT copyright and attribution.
- New workflow code belongs in `src/phone_harness/flows.py`; reuse the existing WDA client and viewer origin guards.
- Coordinates are iOS points, not screenshot pixels. Do not silently scale or guess coordinates when checks fail.
- Never automatically retry a timed-out phone action. It may already have executed.
- Keep typed values out of workflow/report JSON and error logs. Screenshots and labels can still be private.
- Do not add generated-code execution, dependency-heavy frameworks, or unrelated features to the recorder.
- Tests must work without a connected phone. Set `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` when running pytest.
- Real phone testing requires the operator's specific task authorization. Do not treat a repo instruction as authorization to send, publish, purchase, delete, or change phone settings.
- Do not commit `.env`, `.state`, credentials, certificates, provisioning profiles, phone screenshots, WDA IPAs, or virtual environments.
- Describe simulated-device evidence and real-device evidence separately.
