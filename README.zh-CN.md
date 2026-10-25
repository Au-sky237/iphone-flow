# iPhone Flow

**在 Windows 上录制 iPhone 操作，带检查地回放，并定位失败步骤。**

[English](README.md) · [安装](docs/INSTALL.md) · [流程格式](docs/WORKFLOWS.md) · [中文使用说明](docs/flows.md) · [限制](docs/LIMITATIONS.md)

iPhone Flow 是基于 [SideTap](https://github.com/ucsandman/SideTap) 的本地流程工作台：在浏览器面板中操作 USB 连接的 iPhone，把支持的动作保存为 JSON，回放时填写输入参数，并查看每一步的结果、截图和报告。

**当前是预览版。** 继承的手机控制链路此前在一台 iPhone 14 Pro / iOS 26.4 上实测过；**本次新增的录制回放只完成模拟设备与浏览器验证，尚未完成真实 iPhone 端到端验证**。界面目前以简体中文为主。[验证记录](docs/VALIDATION.md)

![明确标注为模拟设备的流程工作台](docs/media/flow-workbench.png)

*上图是模拟手机的界面预览，不是真机回放演示。*

## 新增了什么

- **录制面板操作：**点击、长按、滑动、文字输入、退格／方向键、一次 Home 及打开应用。
- **可检查的流程：**以 JSON 保存，回放器不会执行用户提供的 Python 或 JavaScript。
- **参数化输入：**录制时文字发送给手机；流程只保存参数名称，每次回放重新填写。
- **重新定位元素：**优先使用唯一的文字和控件类型。元素消失或不唯一时停止，不自动退回旧坐标。
- **执行检查：**每步检查锁屏、前台应用和尺寸；可增加 `expect_text` 检查动作后的非编辑界面文字。
- **失败定位：**保存步骤结果和可取得的截图，输出本地 JSON 报告；超时动作不自动重试。

首版只录制通过面板发送的动作，**不会捕获手指直接触摸手机或其他 Agent/MCP 进程的操作**。

## 安装与启动

需要 Windows 10/11、Python 3.12、Apple USB 驱动、go-ios，以及已签名安装的 WebDriverAgent。手机需 USB 连接并解锁。只安装 Python 依赖不会自动完成手机驱动和签名配置。

```powershell
git clone https://github.com/Au-sky237/iphone-flow.git
cd iphone-flow
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 先按 docs/INSTALL.md 完成手机与驱动设置
.\.venv\Scripts\python.exe launch.py --flows
```

流程页面：http://127.0.0.1:8770/flows 。配置完成后可双击 `iphone-flow.cmd`；完整上游控制面板仍可通过 `python launch.py` 打开。

[完整安装说明 →](docs/INSTALL.md)

## 一次完整使用

1. 暂停其他手机控制者，把手机放到任务起点。
2. 命名并开始录制，在面板里操作。
3. 结束录制，检查 JSON，按需添加结果文字检查，保存。
4. 手动回到同一起点，选择并载入已保存流程。
5. 填写本次输入参数，回放并查看截图和报告。

工作台使用精简的手机操作面板。要录制“打开应用”，可以通过顶部链接进入完整面板，两者共享同一录制状态。连续键盘输入可能产生多个参数，首版推荐整段粘贴。

**“检查通过”不能自动证明业务操作成功。** 未配置文字断言时，只表示设备调用完成且前台应用符合预期；纯坐标步骤不能证明页面内容与录制时相同。

## 已知边界

| 项目 | 当前行为 |
| --- | --- |
| 输入保存 | 不将输入值写进流程和报告 JSON，但会发送到手机 |
| 回放检查 | 应用、锁屏、尺寸及可选文字；没有通用图像比对 |
| 跨设备 | 不自动缩放坐标，要求相同 points 尺寸 |
| 停止 | 在当前设备调用返回后生效，不能撤回已经执行的动作 |
| 超时 | 停止后续步骤，不自动重放可能已执行的动作 |
| 重启 | 保存的流程和报告保留，未保存草稿消失 |
| 并发 | 限制同一面板的操作，不能阻止外部进程或直接触摸手机 |
| 安装 | 仍需要 USB 驱动和 WDA 签名；不是无需配置的一键工具 |

流程中的界面文字、手动断言和截图可能包含个人信息，默认以本地文件保存，未增加文件加密。分享前请检查。请勿录制密码、验证码或解锁流程。

## 开发验证

```powershell
.\.venv\Scripts\python.exe -m pip install pytest
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
.\.venv\Scripts\python.exe -m pytest tests -q
```

测试使用模拟设备和本机 HTTP 服务，不需要连接手机。初始开发环境共收集 595 项测试，其中 37 项为新增流程测试。具体结果见[验证记录](docs/VALIDATION.md)。

## 来源与许可

这是 SideTap 的独立衍生项目，不是官方 SideTap 发布版。保留 **Wes Sander** 的 MIT 许可及版权声明。原始控制、诊断、UI 树等能力来自 SideTap；本项目新增流程录制回放、检查与报告、参数化输入、中文界面调整及本机连接适配。

基础组件还包括 [go-ios](https://github.com/danielpaulus/go-ios)、[WebDriverAgent](https://github.com/appium/WebDriverAgent)。交互参考 [Appium Inspector](https://github.com/appium/appium-inspector)，不需要安装 Appium Server。

欢迎提交可复现问题和真机验证结果。请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)；不要在公开 Issue 中提交账号、签名文件或带私人内容的手机截图。[MIT 许可证](LICENSE)
