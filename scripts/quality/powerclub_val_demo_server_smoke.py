#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import threading
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SERVER = ROOT / "tools" / "powerclub_val_demo_server.py"


def load_server():
    spec = importlib.util.spec_from_file_location("powerclub_val_demo_server", SERVER)
    if spec is None or spec.loader is None:
        raise AssertionError("could not load PowerClub Val demo server")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_url(url: str) -> tuple[int, str]:
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8")


def post_json(url: str, payload: dict) -> tuple[int, dict]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def assert_true(value: bool, label: str) -> None:
    if not value:
        raise AssertionError(label)


def main() -> int:
    server_module = load_server()
    old_mock = os.environ.get(server_module.MOCK_ENV)
    os.environ[server_module.MOCK_ENV] = "1"
    httpd = server_module.create_server("127.0.0.1", 0)
    host, port = httpd.server_address
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    base = f"http://{host}:{port}"
    try:
        status, health = read_url(f"{base}/powerclub/val/health")
        assert_true(status == 200, "health status ok")
        assert_true('"mode": "mock"' in health, "health reports mock mode")

        status, html = read_url(f"{base}/val_discovery.html")
        assert_true(status == 200, "Val Discovery served")
        assert_true("Sugerir con Val" in html, "Val Discovery has LLM suggestion seam")

        payload = {
            "meeting_context": {"client_or_person": "PowerClub"},
            "current_question": "¿Dónde se pierden más oportunidades?",
            "captured_response": "El seguimiento llega tarde.",
            "selected_category": "seguimiento",
            "whiteboard_state": {},
            "allowed_demo_sections": list(server_module.ALLOWED_DEMO_SECTIONS),
            "guardrails": ["Frank approves"],
        }
        status, body = post_json(f"{base}/powerclub/val/mentor-suggest", payload)
        assert_true(status == 200, "mentor suggest returns ok in mock mode")
        assert_true(body.get("status") == "ok", "mentor suggest body ok")
        assert_true(body.get("mode") == "mock", "mentor suggest body mock")
        suggestion = body.get("suggestion") or {}
        assert_true(suggestion.get("needs_frank_confirmation") is True, "Frank confirmation required")
        assert_true(suggestion.get("recommended_demo_section") == "Riesgo y rescate", "demo section mapped")
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)
        if old_mock is None:
            os.environ.pop(server_module.MOCK_ENV, None)
        else:
            os.environ[server_module.MOCK_ENV] = old_mock

    print("PASS: PowerClub Val demo server smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
