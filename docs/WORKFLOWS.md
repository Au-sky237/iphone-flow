# Workflow format (version 1)

Workflows are validated data, not executable scripts. Paste JSON into the
workbench editor and save it as a new flow. Loading a flow does not run it.
The preview editor creates a new saved file rather than overwriting an old one.

```json
{
  "version": 1,
  "name": "Example tap",
  "steps": [
    {
      "action": "tap",
      "before": { "app": "com.example.app", "size": [393, 852] },
      "args": { "x": 120, "y": 300 },
      "locator": { "text": "Continue", "type": "Button" },
      "after_app": "com.example.app",
      "expect_text": "Completed"
    }
  ]
}
```

`com.example.app`, coordinates, dimensions and text above are illustrative.
Record actual values for your device.

## Fields

- `version`: currently `1`.
- `name`: a non-empty name, at most 120 characters.
- `steps`: 1–200 steps.
- `before.app`: the foreground bundle ID expected before the action.
- `before.size`: `[width, height]` in iOS **points**, not screenshot pixels.
- `action` and `args`: one of the supported actions below.
- `after_app`: expected foreground bundle ID after the action.
- `locator`: optional exact text/type match for a tap or long press.
- `expect_text`: optional substring in visible, non-editable UI text after the
  action, up to 500 characters. This is not an OCR or image assertion.

Unknown fields are discarded when saving. Custom executable code is not
supported. A syntactically valid workflow can still contain unsuitable actions;
inspect every flow before replaying it.

## Actions

| Action | `args` |
| --- | --- |
| `tap` | `x`, `y` |
| `long_press` | `x`, `y`, `seconds` |
| `swipe` | `x1`, `y1`, `x2`, `y2`, `seconds` |
| `type` | `parameter`, such as `text2` |
| `key` | `key`: W3C backspace or arrow-key value |
| `home` | `{}`; one Home press |
| `open_app` | `bundle`: installed app bundle ID |

Coordinates must be finite numbers within the recorded screen. Gesture
duration must be within 0.05–3 seconds. Supported key values are `\ue003`
(backspace), `\ue012` (left), `\ue013` (up), `\ue014` (right), `\ue015` (down).
Submit actions should be recorded as a deliberate tap on the phone's button;
the panel's automatic Enter-to-Send behavior is not recorded in this version.

## Input parameters

```json
{
  "action": "type",
  "before": { "app": "com.example.app", "size": [393, 852] },
  "args": { "parameter": "search_query" },
  "after_app": "com.example.app"
}
```

The workbench asks for `search_query` before replay. It types into the current
focus; it does not clear the field or verify complete typed content. Record the
appropriate field-selection/clearing actions and validate results separately.
Multiple steps may share a parameter. Names must begin with an ASCII letter
and contain only letters, digits or underscores, up to 40 characters.

Values are held for that run and are not deliberately written into workflow or
report JSON. They can appear on the phone and in screenshots. Do not use this
to record passwords, one-time codes, or unlock operations.

## Execution and reports

The runner checks the phone is unlocked, app and dimensions match, then
resolves any locator uniquely. It never falls back to stored coordinates if a
saved locator becomes invalid. A coordinate-only action cannot establish that
the intended screen is still showing.

After the action, app/optional text observation is polled for up to five
seconds between reads. Individual device reads have their own timeout and may
extend wall-clock duration. Observation may repeat; **the action does not**.

Each report includes run ID, flow ID/name, status, step index/action/status,
available screenshot filenames, and an error where applicable. It is saved
under `.state/flows/runs/<run-id>/report.json`; images are `step-N.png`.
No report is automatically resumed after process restart.

Passing an app/text check is evidence for that check only, not a guarantee of
a successful transaction, submission, or task. Cancellation stops subsequent
work when the current device call returns. It cannot undo a submitted action.
