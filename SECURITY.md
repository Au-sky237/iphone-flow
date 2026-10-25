# Security and local data

This preview drives a real phone with the privileges of its installed
WebDriverAgent. Keep the viewer and USB-forwarded ports on loopback. WDA does
not provide a user-account authentication layer for these local operations.

The workflow UI stores flows and reports locally under `.state/flows` by
default. Typed parameter values are not deliberately persisted in workflow or
report JSON, and driver error text is redacted by the replay runner. This is
not a promise that data can never appear on the phone, in a screenshot, in an
element label, in a manually written assertion, or in inherited/external tools.

Files are not additionally encrypted by this feature. Do not record passwords,
verification codes, or unlock sequences. Review screenshots, workflows, and
reports before sharing. Do not expose the viewer or WDA ports to the Internet.

Cancellation cannot revoke a command already sent to the device. External
controllers and direct phone touches are outside the replay lock.

Do not post credentials or exploit details containing private phone data in a
public issue. If private security reporting is available on GitHub, use it;
otherwise request a private contact method without including sensitive details.
