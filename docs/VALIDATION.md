# Validation record

Recorded on **2026-10-25** during preparation of `0.1.0-preview`.

## Previously exercised control stack

The existing SideTap deployment had previously demonstrated screenshots, taps,
swipes, typing and launching apps on one iPhone 14 Pro / iOS 26.4 from Windows.
That evidence belongs to the control stack, not to the new workflow runner.

## New workflow tests

37 new tests cover recording, save/load, unique element relocation, missing and
duplicate locators, locked/wrong-app/rotated-screen preconditions, invalid
coordinates and paths, parameter requirements, input/error redaction,
cancellation, STOP, screenshot failure, optional text assertions, post-action
checks without action retry, and local HTTP integration/origin checks.

The complete initial development suite collected 595 tests. One full run
finished with 594 passes and one existing cross-origin rejection test reporting
a Windows loopback connection reset. That case passed when rerun alone without
production-code changes. This is not represented as a single uninterrupted
595-pass run.

After the compact workbench adjustment, the 37 workflow tests plus two viewer
HTML/JavaScript checks passed (39 tests). Existing localization-related literal
assertions were made compatible with the Chinese UI; a clipboard test was
isolated from local optional WDA configuration.

## Browser integration

Using a simulated device, browser automation completed:

1. Starting a recording.
2. Clicking the phone preview and submitting text through the panel.
3. Stopping and saving the two-step flow.
4. Loading the saved flow and entering a fresh parameter value.
5. Replaying and observing two passed steps and report/screenshot links.
6. Checking that the recorded input literal was absent from the workflow JSON.

The workbench was checked at viewport widths 1280, 800 and 390 pixels, with no
top-level horizontal overflow. The preview image in the README uses a clearly
labeled simulated phone.

## Still outstanding

- Real-iPhone end-to-end recording/replay of the new workflow feature.
- An independent Windows machine's setup and signing experience.
- Broader application, device, locale and iOS compatibility.
- Performance measurements for the new recorder under real WDA latency.

CI results after publication are separate evidence and should be read from the
repository's Actions page. A green mock-device suite does not close the
real-device validation gap.

## Clean publication snapshot

The sanitized publication directory, without the development machine's `.env`
or `.state`, completed **595 passed in 90.09 seconds** on Windows / Python
3.12.14. Header-only rejection tests use empty request bodies to avoid Windows
resetting a connection with unread body bytes before the 403 arrives. Separate
raw HTTP request-smuggling tests remain in the suite. Production origin and
content-type rejection behavior was not weakened to obtain the test result.

Gitleaks 8.30.1 was obtained from its official release and the archive checksum
was verified. A local scan of the publication directory reported no leaks.
An explicit file allowlist excludes local state, credentials, signing material,
virtual environments and device packages. These checks reduce publication
mistakes; they are not a comprehensive security audit.
