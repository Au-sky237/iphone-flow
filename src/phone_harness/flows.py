"""Local, explicit viewer recordings. No code execution or automatic retries."""

from __future__ import annotations

import copy
import json
import math
import re
import threading
import time
import uuid
from pathlib import Path

from . import config
from .wda_client import stop_engaged

ROUTES = {
    "/api/tap": "tap", "/api/swipe": "swipe", "/api/type": "type",
    "/api/key": "key", "/api/home": "home", "/api/open-app": "open_app",
    "/api/long_press": "long_press",
}


class FlowError(ValueError):
    pass


def _number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise FlowError("坐标和时间必须是有限数字")
    return value


def _id(value):
    if not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{32}", value):
        raise FlowError("无效的流程或报告编号")
    return value


def _texts(tree):
    from .helpers import collect_texts
    # Exclude editable values from locators. Typed input is never persisted.
    clean = copy.deepcopy(tree)
    stack = [clean]
    while stack:
        node = stack.pop()
        if not isinstance(node, dict):
            continue
        if any(t in str(node.get("type", "")) for t in ("TextField", "TextView", "Secure")):
            node.pop("value", None)
            node.pop("label", None)
            node.pop("name", None)
        stack.extend(node.get("children") or [])
    return collect_texts(clean)


def _locator(tree, x, y):
    rows = _texts(tree)
    hits = []
    for row in rows:
        r = row["rect"]
        if r["x"] <= x <= r["x"] + r["width"] and r["y"] <= y <= r["y"] + r["height"]:
            if row["type"].endswith(("Application", "Window")):
                continue
            same = [e for e in rows if e["text"] == row["text"] and e["type"] == row["type"]]
            if len(same) == 1:
                hits.append(row)
    if not hits:
        return None
    best = min(hits, key=lambda e: e["rect"]["width"] * e["rect"]["height"])
    return {"text": best["text"], "type": best["type"]}


def validate(flow):
    if not isinstance(flow, dict) or flow.get("version") != 1:
        raise FlowError("仅支持 version: 1 的流程")
    name = flow.get("name")
    steps = flow.get("steps")
    if not isinstance(name, str) or not name.strip() or len(name) > 120:
        raise FlowError("流程名称必须为 1–120 个字符")
    if not isinstance(steps, list) or not 1 <= len(steps) <= 200:
        raise FlowError("流程需要 1–200 个步骤")
    result = {"version": 1, "name": name.strip(), "steps": []}
    for step in steps:
        if not isinstance(step, dict) or step.get("action") not in ROUTES.values():
            raise FlowError("包含不支持的动作")
        action = step["action"]
        before = step.get("before", {})
        if not isinstance(before, dict) or not isinstance(before.get("app"), str) or not before["app"]:
            raise FlowError("每一步需要 before.app")
        size = before.get("size")
        if not isinstance(size, list) or len(size) != 2 or any(_number(n) <= 0 for n in size):
            raise FlowError("每一步需要有效屏幕尺寸 before.size")
        after = step.get("after_app")
        if not isinstance(after, str) or not after:
            raise FlowError("每一步需要 after_app")
        out = {"action": action, "before": {"app": before["app"], "size": size}, "after_app": after}
        args = step.get("args", {})
        if not isinstance(args, dict):
            raise FlowError("args 必须为对象")
        if action in ("tap", "long_press", "swipe"):
            keys = ("x1", "y1", "x2", "y2") if action == "swipe" else ("x", "y")
            out["args"] = {k: _number(args.get(k)) for k in keys}
            for k, value in out["args"].items():
                bound = size[0 if k.startswith("x") else 1]
                if not 0 <= value < bound:
                    raise FlowError("坐标超出录制屏幕")
            if action != "tap":
                seconds = _number(args.get("seconds", 0.3 if action == "swipe" else 0.8))
                if not 0.05 <= seconds <= 3:
                    raise FlowError("手势时间应在 0.05–3 秒之间")
                out["args"]["seconds"] = seconds
            locator = step.get("locator")
            if locator is not None:
                if action == "swipe" or not isinstance(locator, dict) or any(
                    not isinstance(locator.get(k), str) or not locator[k] for k in ("text", "type")
                ):
                    raise FlowError("无效的元素定位信息")
                out["locator"] = {k: locator[k] for k in ("text", "type")}
        elif action == "type":
            parameter = args.get("parameter")
            if not isinstance(parameter, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,39}", parameter):
                raise FlowError("输入步骤需要 parameter 名称")
            out["args"] = {"parameter": parameter}
        elif action == "key":
            key = args.get("key")
            if key not in ("\ue003", "\ue012", "\ue013", "\ue014", "\ue015"):
                raise FlowError("只支持退格和方向键；提交请录制按钮点击")
            out["args"] = {"key": key}
        elif action == "open_app":
            bundle = args.get("bundle")
            if not isinstance(bundle, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+", bundle):
                raise FlowError("打开应用需要 bundle ID")
            out["args"] = {"bundle": bundle}
        else:
            out["args"] = {}
        expected = step.get("expect_text", "")
        if not isinstance(expected, str) or len(expected) > 500:
            raise FlowError("expect_text 需要为不超过 500 字的文字")
        if expected:
            out["expect_text"] = expected
        result["steps"].append(out)
    return result


def _context(client):
    if client.is_locked():
        raise FlowError("手机已锁屏，请手动解锁后重新开始")
    app = client.active_app().get("bundleId")
    if not app:
        raise FlowError("无法确认前台应用，已停止")
    return {"app": app, "size": list(client.window_size())}


def _execute(client, step, inputs, replay=False):
    args = dict(step["args"])
    action = step["action"]
    if replay:
        current = _context(client)
        if current["app"] != step["before"]["app"]:
            raise FlowError("前台应用与录制不符，请回到录制起点")
        if current["size"] != step["before"]["size"]:
            raise FlowError("屏幕尺寸或方向与录制不符")
        locator = step.get("locator")
        if locator:
            matches = [e for e in _texts(client.source()) if e["text"] == locator["text"] and e["type"] == locator["type"]]
            if len(matches) != 1:
                raise FlowError("录制元素不存在或不唯一，未退回坐标盲点")
            args.update(x=matches[0]["x"], y=matches[0]["y"])
    if action == "type":
        text = inputs[args["parameter"]]
        if config.PHONE_PASSCODE and config.PHONE_PASSCODE in text:
            raise FlowError("流程不用于输入手机解锁码")
        client.type_text(text)
    elif action == "home":
        client.press_button("home")
    elif action == "open_app":
        client.app_launch(args["bundle"])
    elif action == "key":
        client.key_press(args["key"])
    else:
        getattr(client, action)(**args)


class FlowStore:
    def __init__(self, root=None):
        self.root = Path(root) if root else config.STATE_DIR / "flows"
        self.lock = threading.RLock()
        self.recording = False
        self.draft = {"version": 1, "name": "新流程", "steps": []}
        self.last_error = ""
        self.run = None
        self.cancel = threading.Event()

    def snapshot(self):
        with self.lock:
            return copy.deepcopy({"recording": self.recording, "draft": self.draft,
                                  "error": self.last_error, "run": self.run})

    def listing(self):
        with self.lock:
            rows = []
            if self.root.exists():
                for path in sorted(self.root.glob("*.json")):
                    if re.fullmatch(r"[a-f0-9]{32}", path.stem):
                        try:
                            f = self.load(path.stem)
                            rows.append({"id": path.stem, "name": f["name"], "steps": len(f["steps"])})
                        except (ValueError, OSError):
                            continue
            return rows

    def load(self, identifier):
        return validate(json.loads((self.root / f"{_id(identifier)}.json").read_text(encoding="utf-8")))

    def save(self, flow, identifier=None):
        checked = validate(flow)
        with self.lock:
            if self.recording or (self.run and self.run["status"] == "running"):
                raise FlowError("请先停止录制或等待回放结束")
            identifier = _id(identifier) if identifier else uuid.uuid4().hex
            self.root.mkdir(parents=True, exist_ok=True)
            target = self.root / f"{identifier}.json"
            pending = target.with_suffix(".tmp")
            pending.write_text(json.dumps(checked, ensure_ascii=False, indent=2), encoding="utf-8")
            pending.replace(target)
            return identifier

    def start(self, name):
        with self.lock:
            if self.recording or (self.run and self.run["status"] == "running"):
                raise FlowError("已有录制或回放正在进行")
            if not isinstance(name, str) or not name.strip() or len(name) > 120:
                raise FlowError("请填写 1–120 字的名称")
            self.draft = {"version": 1, "name": name.strip(), "steps": []}
            self.last_error = ""
            self.recording = True

    def stop(self):
        with self.lock:
            self.recording = False

    def record(self, client, path, payload):
        with self.lock:
            if not self.recording:
                raise FlowError("录制已结束，请重新操作")
            try:
                if len(self.draft["steps"]) >= 200:
                    raise FlowError("已达到 200 步上限")
                action = ROUTES[path]
                before = _context(client)
                args = dict(payload)
                inputs = {}
                if action == "type":
                    parameter = f"text{len(self.draft['steps']) + 1}"
                    inputs[parameter] = str(args.get("text", ""))
                    args = {"parameter": parameter}
                elif action == "open_app":
                    from .helpers import _resolve_bundle
                    args = {"bundle": _resolve_bundle(str(args.get("name", "")))}
                step = {"action": action, "args": args, "before": before, "after_app": before["app"]}
                if action in ("tap", "long_press"):
                    locator = _locator(client.source(), float(args["x"]), float(args["y"]))
                    if locator:
                        step["locator"] = locator
                step = validate({"version": 1, "name": "check", "steps": [step]})["steps"][0]
                _execute(client, step, inputs)
                # A transport success is not proof that the intended UI changed.
                step["after_app"] = _context(client)["app"]
                self.draft["steps"].append(step)
            except Exception:
                self.recording = False
                self.last_error = "录制已停止：动作或观察失败。该动作可能已执行，请检查手机；失败动作未保存。"
                raise FlowError(self.last_error) from None

    def begin_run(self, identifier, inputs, client, slot):
        flow = self.load(identifier)
        required = {s["args"]["parameter"] for s in flow["steps"] if s["action"] == "type"}
        if not isinstance(inputs, dict) or any(not isinstance(inputs.get(k), str) for k in required):
            raise FlowError("请填写全部输入参数")
        inputs = {k: inputs[k] for k in required}
        with self.lock:
            if self.recording or (self.run and self.run["status"] == "running"):
                raise FlowError("请先停止当前录制或回放")
            self.cancel.clear()
            self.run = {"id": uuid.uuid4().hex, "flow_id": identifier, "name": flow["name"],
                        "status": "running", "steps": [], "total": len(flow["steps"]), "error": ""}
            threading.Thread(target=self._play, args=(flow, inputs, client, slot), daemon=True).start()
            return self.run["id"]

    def _play(self, flow, inputs, client, slot):
        run = self.run
        report_dir = self.root / "runs" / run["id"]
        try:
            report_dir.mkdir(parents=True, exist_ok=True)
            with slot():
                for index, step in enumerate(flow["steps"], 1):
                    row = {"index": index, "action": step["action"], "status": "running"}
                    with self.lock:
                        run["steps"].append(row)
                    try:
                        if self.cancel.is_set() or stop_engaged():
                            raise FlowError("用户停止回放")
                        _execute(client, step, inputs, replay=True)
                        deadline = time.monotonic() + 5
                        while True:
                            if self.cancel.is_set() or stop_engaged():
                                raise FlowError("用户停止回放")
                            after = _context(client)
                            good = after["app"] == step["after_app"]
                            if good and step.get("expect_text"):
                                good = any(step["expect_text"] in e["text"] for e in _texts(client.source()))
                            if good:
                                break
                            if time.monotonic() >= deadline:
                                raise FlowError("执行后应用或文字检查未通过；动作不会自动重放")
                            time.sleep(0.25)
                        row["status"] = "passed"
                    except Exception as exc:
                        row["status"] = "failed"
                        # Driver errors may echo typed values: persist a fixed message.
                        row["error"] = str(exc) if isinstance(exc, FlowError) else "设备动作或读取失败；动作可能已执行，请查看手机"
                        raise FlowError(row["error"]) from None
                    finally:
                        try:
                            filename = f"step-{index}.png"
                            (report_dir / filename).write_bytes(client.screenshot())
                            row["screenshot"] = filename
                        except Exception:
                            row["screenshot_error"] = "设备未能提供截图"
            with self.lock:
                run["status"] = "passed"
        except Exception as exc:
            with self.lock:
                run["status"] = "stopped" if self.cancel.is_set() or stop_engaged() else "failed"
                run["error"] = str(exc) if isinstance(exc, FlowError) else "无法取得设备或保存报告"
        finally:
            inputs.clear()
            with self.lock:
                try:
                    (report_dir / "report.json").write_text(json.dumps(run, ensure_ascii=False, indent=2), encoding="utf-8")
                except OSError:
                    run["error"] += "；报告写入失败"

    def report_file(self, identifier, filename):
        _id(identifier)
        if not re.fullmatch(r"(?:report\.json|step-[1-9][0-9]{0,2}\.png)", filename):
            raise FlowError("无效的报告文件")
        return self.root / "runs" / identifier / filename


store = FlowStore()
