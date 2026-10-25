# Attribution and source lineage

This repository is an independently maintained derivative source snapshot of
[ucsandman/SideTap](https://github.com/ucsandman/SideTap), based on upstream commit
`bc43e6f56b199a28c44ca6f696fba42e5f2194a4`.

SideTap's original copyright is **Copyright (c) 2026 Wes Sander**. Its original
MIT license is preserved verbatim in `LICENSE`. This repository does not claim
ownership of the inherited Windows/iPhone control stack, diagnostic system,
Agent/MCP integration, or the original viewer and tests.

The derived work adds a panel-driven workflow recorder and replay runner,
parameterized input, precondition checks and optional post-action text checks,
step reports/screenshots, a workflow UI, tests, Chinese localization, and local
USB forwarding/process-output changes. Changes prepared for this publication
are maintained by Au-sky237.

SideTap credits ShawnPana/phone-harness for the original macOS concept,
danielpaulus/go-ios for USB transport, and appium/WebDriverAgent for iOS
automation. The new recorder's interaction model was informed by the public
Appium Inspector recorder documentation; no Appium Inspector implementation is
included.

No signed WebDriverAgent package, Apple certificate, provisioning profile,
private account configuration, phone data, runtime state, or local virtual
environment is included in this source snapshot. External tools retain their
respective licenses. This is not an official release of SideTap, Appium, or
Apple software and makes no claim of endorsement by their maintainers.
