# Windows setup / Windows 安装

This is a source preview. There is no bundled installer or signed WDA binary.
日常使用不需要 Mac，但必须先在手机上完成 WebDriverAgent 签名与安装。

## Requirements

- Windows 10/11, Python 3.12 and Git.
- Apple Devices from the Microsoft Store, or a compatible Apple USB driver.
- A USB-connected, trusted, unlocked iPhone. SideTap targets iOS 17+; the new
  workflow feature's real-device compatibility is still unverified.
- [go-ios](https://github.com/danielpaulus/go-ios), available as `ios.exe`.
- [WebDriverAgent](https://github.com/appium/WebDriverAgent), signed and installed
  for your phone. Signing tools and Apple accounts are not included.

## 1. Prepare the source

Example location on D:, with a local Python environment:

```powershell
New-Item -ItemType Directory -Force D:\Projects | Out-Null
Set-Location D:\Projects
git clone https://github.com/Au-sky237/iphone-flow.git
Set-Location iphone-flow
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

You do not need to copy `.env.example` for the default ports. If you need
overrides, copy it to `.env` and fill only those values. Never share that file.

## 2. Install the Windows USB tools

Install Apple's USB driver and connect the phone. Unlock it and accept **Trust
This Computer** on the phone when prompted. Enable Developer Mode under
**Settings → Privacy & Security → Developer Mode** if your iOS version requires
it, including any restart/confirmation shown on the phone.

Obtain the Windows go-ios executable from its official project. Put `ios.exe`
and any companion files required by that release in `tools\bin`, or install it
using the upstream project's documented method. Test it before proceeding:

```powershell
$env:PATH = "$PWD\tools\bin;" + $env:PATH
$env:GO_IOS_AGENT_PORT = '28100'
ios --version
ios list
```

`tools` is ignored by Git. This repository does not redistribute go-ios.
Follow go-ios release documentation for additional tunnel-driver requirements.

## 3. Sign and install WebDriverAgent

Use an appropriate WDA build and a signing tool you trust, such as the method
described by [SideTap's upstream setup guide](https://github.com/ucsandman/SideTap/blob/main/docs/setup-windows.md).
Check the source and compatibility of the WDA package. This repository does not
include a signed IPA, Apple identity, provisioning profile, or signing service.

Keep WDA's XCTest extension intact: removing extensions while re-signing can
remove the test runner that the control connection needs. Trust the appropriate
developer identity under **Settings → General → VPN & Device Management** if
iOS requests it. Keep the phone unlocked for installation.

Free Apple-account signatures are time limited (commonly seven days). Signing
and renewal are separate from workflow recording; the recorder does not remove
Apple's signing requirement.

If auto-detection cannot locate your WDA runner, set `WDA_BUNDLE_ID` in `.env`.
Use your actual installed runner ID, not a copied value from someone else's
phone.

## 4. Diagnose, then launch

```powershell
$env:PYTHONPATH = "$PWD\src"
$env:PATH = "$PWD\tools\bin;" + $env:PATH
$env:GO_IOS_AGENT_PORT = '28100'
.\.venv\Scripts\python.exe -m phone_harness doctor
.\.venv\Scripts\python.exe launch.py --flows
```

The inherited diagnostics identify missing pieces of the USB/tunnel/WDA chain.
Follow the specific error before retrying. Starting the panel is not evidence
that WDA signing or input control is ready.

The workflow workbench opens at **http://127.0.0.1:8770/flows**. After setup,
double-click `iphone-flow.cmd`. The original panel is at `/`.

Starting the application replaces an existing SideTap viewer process tracked
by the same state directory. Finish other phone work before restarting it.
Use one controller at a time when recording or replaying.

## 5. First replay

Record a short, reversible flow with non-sensitive data. Return to the starting
screen before replaying. Inspect the screenshot report. Add `expect_text` checks
for results you need to verify; an app match alone cannot prove completion.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| No phone detected | Driver, USB cable, unlock state, and computer trust |
| Screen works, input does not | Signed WDA installation, trust, signature expiry, XCTest extension |
| Tunnel cannot bind | Existing process/port, go-ios tunnel setup, and port 28100 |
| Replay stops before step 1 | Starting app, point dimensions, orientation, lock state |
| Recorded element missing | App layout/text changed, wrong starting page, or duplicate labels |
| Device call times out | Inspect the phone; do not assume the action failed to execute |

Do not switch a failed element lookup to blind coordinate clicks just to make
a test pass. See [limitations](LIMITATIONS.md) and upstream-derived
[diagnostic history](ERRORS.md). Historical measurements are not performance
promises for your device.
