# Preview limitations

## Evidence

The new workflow feature has not yet completed a real-device end-to-end test.
Simulated-device test results and UI screenshots are labeled accordingly.
The inherited control stack's prior success on one device does not establish
compatibility with every iPhone, iOS version, or application.

## Recording

- Only supported HTTP actions from the local viewer are recorded.
- Direct finger touches and other Agent/MCP processes are outside recording.
- Other controller processes may interfere with recorded context or replay.
- Composite panel actions, clipboard operations, automatic Enter-to-Send,
  lock/unlock, and console commands are not recorder actions. Unsupported
  operations are rejected while recording; stop recording to use them.
- Home means one Home press. It does not reproduce the full panel's optional
  walk back to Home Screen page one.
- Continuous keyboard input can become several parameter steps.
- The in-memory recording draft is lost on restart. Save before restarting.

## Replay

- No coordinate scaling, adaptive image recognition or self-healing scripts.
- Text labels and app layouts can change with locale, version and dynamic data.
- Uniqueness by text/type is a useful check, not proof of semantic identity.
- Coordinate-only steps check app and dimensions, not complete page contents.
- Text assertions inspect non-editable accessibility text. They cannot verify
  password-field contents, an image-only interface, or full business success.
- Every replay starts from step one, with the phone restored manually.
- Cancellation waits for a device call to finish; already-issued actions cannot
  be revoked. A timeout leaves action outcome uncertain and stops the flow.
- No background schedule, task queue, cross-device fleet or unattended service
  is added by the workflow feature.

## Setup and data

- USB drivers, go-ios and signed WDA are still required.
- Signature renewal remains an Apple/signing-tool concern.
- The inherited auto-recovery/diagnostic routines have their own behavior;
  they do not establish that a failed task succeeded.
- Screenshots and labels can contain private data. Flow files/reports are
  local, plain files; the feature adds no encryption or hosted backup.
- Optional upstream controls such as unlocking, messaging and photo import
  remain in the full panel. Their existence does not authorize an Agent to use
  them for an unrelated task.
