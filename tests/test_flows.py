"""Workflow failure boundaries and HTTP integration, without a phone."""

import contextlib
import copy
import json
import sys
import threading
import time
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest
import requests

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from phone_harness import flows, viewer


def tree(label="设置", x=10):
    return {"type": "Application", "children": [
        {"type": "Button", "label": label, "rect": {"x": x, "y": 10, "width": 50, "height": 30}}
    ]}


class Phone:
    def __init__(self):
        self.calls = []
        self.app = "com.example.demo"
        self.size = [390, 844]
        self.locked = False
        self.tree = tree()
        self.fail = False

    def is_locked(self):
        return self.locked

    def active_app(self):
        return {"bundleId": self.app}

    def window_size(self):
        return self.size

    def source(self):
        return self.tree

    def screenshot(self):
        return b"fake png"

    def tap(self, x, y):
        self.calls.append(("tap", x, y))
        if self.fail:
            raise TimeoutError("private text echoed by driver")

    def type_text(self, text):
        self.calls.append(("type", text))
        if self.fail:
            raise TimeoutError(text)

    def swipe(self, **args):
        self.calls.append(("swipe", args))

    def key_press(self, key):
        self.calls.append(("key", key))

    def press_button(self, button):
        self.calls.append(("home", button))
        self.app = "com.apple.springboard"

    def app_launch(self, bundle):
        self.calls.append(("open_app", bundle))
        self.app = bundle


def flow(action="tap", args=None):
    return {"version": 1, "name": "测试流程", "steps": [{
        "action": action, "args": {"x": 20, "y": 20} if args is None else args,
        "before": {"app": "com.example.demo", "size": [390, 844]},
        "after_app": "com.example.demo",
    }]}


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setattr(flows, "stop_engaged", lambda: False)
    monkeypatch.setattr(flows.config, "PHONE_PASSCODE", None)
    return flows.FlowStore(tmp_path / "flows")


def wait_run(store):
    deadline = time.monotonic() + 4
    while time.monotonic() < deadline:
        state = store.snapshot()["run"]
        if state and state["status"] != "running":
            # Wait for the report to finish too, rather than racing file IO.
            path = store.report_file(state["id"], "report.json")
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8"))
        time.sleep(0.01)
    pytest.fail("background run did not finish")


def play(store, phone, value=None, inputs=None):
    identifier = store.save(value or flow())
    store.begin_run(identifier, inputs or {}, phone, contextlib.nullcontext)
    return wait_run(store)


def test_record_move_locator_and_replay(store):
    phone = Phone()
    store.start("设置检查")
    store.record(phone, "/api/tap", {"x": 20, "y": 20})
    store.stop()
    assert store.draft["steps"][0]["locator"] == {"text": "设置", "type": "Button"}
    phone.calls.clear()
    phone.tree = tree(x=100)
    result = play(store, phone, store.draft)
    assert result["status"] == "passed"
    assert phone.calls == [("tap", 125, 25)]
    assert result["steps"][0]["screenshot"] == "step-1.png"


@pytest.mark.parametrize("change", ["app", "size", "locked", "missing", "duplicate"])
def test_failed_preconditions_never_tap(store, change):
    phone = Phone()
    value = flow()
    value["steps"][0]["locator"] = {"text": "设置", "type": "Button"}
    if change == "app":
        phone.app = "com.other.app"
    elif change == "size":
        phone.size = [844, 390]
    elif change == "locked":
        phone.locked = True
    elif change == "missing":
        phone.tree = tree("其他")
    else:
        phone.tree["children"] *= 2
    result = play(store, phone, value)
    assert result["status"] == "failed"
    assert not phone.calls
    assert result["steps"][0]["screenshot"]


def test_timeout_not_retried_and_error_redacted(store):
    phone = Phone()
    phone.fail = True
    value = flow()
    value["steps"] *= 2
    result = play(store, phone, value)
    assert len(phone.calls) == 1
    assert len(result["steps"]) == 1
    assert "private text" not in json.dumps(result)


def test_text_is_parameter_not_saved(store):
    phone = Phone()
    secret = "only-in-memory-123"
    store.start("输入")
    store.record(phone, "/api/type", {"text": secret})
    store.stop()
    assert secret not in json.dumps(store.snapshot())
    identifier = store.save(store.draft)
    assert secret not in (store.root / f"{identifier}.json").read_text(encoding="utf-8")
    store.begin_run(identifier, {"text1": secret}, phone, contextlib.nullcontext)
    result = wait_run(store)
    assert secret not in json.dumps(result)
    assert phone.calls == [("type", secret), ("type", secret)]


def test_text_failure_cannot_leak_driver_echo(store):
    phone = Phone()
    phone.fail = True
    result = play(store, phone, flow("type", {"parameter": "text1"}), {"text1": "secret input"})
    assert "secret input" not in json.dumps(result)
    assert result["status"] == "failed"


def test_missing_parameter_never_starts(store):
    identifier = store.save(flow("type", {"parameter": "text1"}))
    with pytest.raises(flows.FlowError):
        store.begin_run(identifier, {}, Phone(), contextlib.nullcontext)
    assert store.run is None


def test_record_failure_stops_and_does_not_save_ambiguous_action(store):
    phone = Phone()
    phone.fail = True
    store.start("失败")
    with pytest.raises(flows.FlowError):
        store.record(phone, "/api/tap", {"x": 20, "y": 20})
    assert not store.recording
    assert not store.draft["steps"]
    assert "private text" not in json.dumps(store.snapshot())


def test_secure_field_not_used_as_locator():
    value = {"type": "SecureTextField", "name": "password", "label": "secret", "value": "secret",
             "rect": {"x": 10, "y": 10, "width": 100, "height": 30}}
    assert flows._locator(value, 20, 20) is None


@pytest.mark.parametrize("identifier", ["../outside", "A" * 32, "", "a/b", None])
def test_invalid_paths_rejected(store, identifier):
    with pytest.raises(flows.FlowError):
        store.load(identifier)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -1, 400, True, "20"])
def test_bad_coordinates_rejected(bad):
    with pytest.raises(flows.FlowError):
        flows.validate(flow(args={"x": bad, "y": 20}))


@pytest.mark.parametrize("action,args", [("exec", {"code": "pass"}), ("type", {"text": "raw"}),
                                         ("key", {"key": "x"}), ("open_app", {"bundle": "../bad"})])
def test_unsupported_or_raw_input_rejected(action, args):
    with pytest.raises(flows.FlowError):
        flows.validate(flow(action, args))


def test_unknown_fields_not_persisted(store):
    value = flow()
    value["password"] = "secret"
    value["steps"][0]["args"]["raw_text"] = "secret"
    identifier = store.save(value)
    assert "secret" not in json.dumps(store.load(identifier))


def test_cancel_between_steps_stops_before_next_action(store):
    phone = Phone()
    tap = phone.tap
    def cancel_after_tap(x, y):
        tap(x, y)
        store.cancel.set()
    phone.tap = cancel_after_tap
    value = flow()
    value["steps"] *= 2
    result = play(store, phone, value)
    assert result["status"] == "stopped"
    assert len(phone.calls) == 1


def test_stop_switch_prevents_first_action(store, monkeypatch):
    monkeypatch.setattr(flows, "stop_engaged", lambda: True)
    phone = Phone()
    assert play(store, phone)["status"] == "stopped"
    assert not phone.calls


def test_failed_screenshot_is_explicit(store):
    phone = Phone()
    def fail_shot():
        raise OSError("offline")
    phone.screenshot = fail_shot
    result = play(store, phone)
    assert result["status"] == "passed"
    assert "screenshot_error" in result["steps"][0]


def test_expected_text_can_pass(store):
    value = flow()
    value["steps"][0]["expect_text"] = "设置"
    assert play(store, Phone(), value)["status"] == "passed"


def test_failed_after_check_does_not_repeat_action(store, monkeypatch):
    clock = iter(range(0, 1000, 6))
    monkeypatch.setattr(flows.time, "monotonic", lambda: next(clock))
    value = flow()
    value["steps"][0]["after_app"] = "com.never.arrives"
    phone = Phone()
    # Synchronous worker avoids mocking the test harness's clock.
    store.run = {"id": "c" * 32, "status": "running", "steps": [], "error": ""}
    store._play(value, {}, phone, contextlib.nullcontext)
    assert store.run["status"] == "failed"
    assert len(phone.calls) == 1


@pytest.fixture
def server(store, monkeypatch):
    monkeypatch.setattr(flows, "store", store)
    phone = Phone()
    monkeypatch.setattr(viewer.Handler, "client", phone)
    monkeypatch.setattr(viewer, "WDAClient", lambda **kw: phone)
    service = ThreadingHTTPServer(("127.0.0.1", 0), viewer.Handler)
    worker = threading.Thread(target=service.serve_forever, daemon=True)
    worker.start()
    yield f"http://127.0.0.1:{service.server_port}", phone
    service.shutdown()
    service.server_close()
    worker.join()


def test_http_record_save_run_report(server, store):
    url, phone = server
    assert requests.get(url + "/flows", timeout=3).status_code == 200
    assert requests.post(url + "/api/flows/start", json={"name": "HTTP"}, timeout=3).status_code == 200
    assert requests.post(url + "/api/tap", json={"x": 20, "y": 20}, timeout=3).json()["ok"]
    stopped = requests.post(url + "/api/flows/stop", json={}, timeout=3).json()
    saved = requests.post(url + "/api/flows/save", json={"flow": stopped["draft"]}, timeout=3).json()
    assert requests.get(url + "/api/flows/get?id=" + saved["id"], timeout=3).json()["flow"]["name"] == "HTTP"
    requests.post(url + "/api/flows/run", json={"id": saved["id"]}, timeout=3).raise_for_status()
    run = wait_run(store)
    assert run["status"] == "passed"
    base = url + "/api/flows/report/" + run["id"]
    assert requests.get(base + "/report.json", timeout=3).json()["status"] == "passed"
    assert requests.get(base + "/step-1.png", timeout=3).content == b"fake png"
    assert requests.get(url + "/api/flows", timeout=3).json()["flows"]


def test_http_recording_rejects_unrecorded_action(server):
    url, phone = server
    requests.post(url + "/api/flows/start", json={"name": "test"}, timeout=3)
    response = requests.post(url + "/api/enter", json={}, timeout=3)
    assert response.status_code == 400
    assert not phone.calls


def test_http_origin_guard_applies_to_flows(server, store):
    url, phone = server
    # No unread body when the origin guard closes the socket (Windows may
    # reset a connection closed with unread data before the 403 is received).
    response = requests.post(url + "/api/flows/start", data=b"",
                             headers={"Origin": "https://example.com", "Content-Type": "application/json"}, timeout=3)
    assert response.status_code == 403
    assert not store.recording


def test_http_missing_flow_is_404(server):
    url, phone = server
    assert requests.get(url + "/api/flows/get?id=" + "a" * 32, timeout=3).status_code == 404
