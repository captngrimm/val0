#!/usr/bin/env python3
from __future__ import annotations

"""
PowerClub Val local browser test harness.

This is a demo-only stdlib server:
- serves docs/demo/powerclub_crm from one origin
- mounts the safe Val Mentor stub endpoint on the same origin
- makes no real provider calls
- stores no data
- creates no production service
"""

import functools
import json
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = Path(__file__).resolve().parent
STATIC_ROOT = ROOT / "docs" / "demo" / "powerclub_crm"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
MAX_BODY_BYTES = 24_000

if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

from powerclub_val_llm_proxy_stub import ALLOWED_DEMO_SECTIONS, MOCK_ENV, handle_mentor_request, truthy


class PowerClubValDemoHandler(SimpleHTTPRequestHandler):
    server_version = "PowerClubValDemoHarness/0.1"

    def _send_json(self, status: int, body: dict[str, Any]) -> None:
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:  # noqa: N802
        if self.path in {"/health", "/powerclub/val/health"}:
            mode = "mock" if truthy(os.getenv(MOCK_ENV)) else "local_fallback"
            self._send_json(
                200,
                {
                    "status": "ok",
                    "service": "powerclub-val-demo-harness",
                    "mode": mode,
                    "static_root": str(STATIC_ROOT),
                },
            )
            return
        if self.path == "/":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/powerclub/val/mentor-suggest":
            self._send_json(404, {"status": "not_found"})
            return

        length = min(int(self.headers.get("Content-Length", "0") or 0), MAX_BODY_BYTES)
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._send_json(
                400,
                {
                    "status": "unavailable",
                    "mode": "local_fallback",
                    "reason": "invalid JSON",
                },
            )
            return

        body = handle_mentor_request(payload)
        self._send_json(200 if body.get("status") == "ok" else 503, body)


def create_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> ThreadingHTTPServer:
    if not STATIC_ROOT.exists():
        raise FileNotFoundError(f"PowerClub demo static root not found: {STATIC_ROOT}")
    handler = functools.partial(PowerClubValDemoHandler, directory=str(STATIC_ROOT))
    return ThreadingHTTPServer((host, port), handler)


def main() -> int:
    host = os.getenv("VAL_POWERCLUB_DEMO_SERVER_HOST", DEFAULT_HOST)
    port = int(os.getenv("VAL_POWERCLUB_DEMO_SERVER_PORT", str(DEFAULT_PORT)))
    server = create_server(host, port)
    actual_host, actual_port = server.server_address
    mock_state = "enabled" if truthy(os.getenv(MOCK_ENV)) else "disabled"
    print(f"PowerClub Val demo harness: http://{actual_host}:{actual_port}/index.html")
    print(f"Val Discovery: http://{actual_host}:{actual_port}/val_discovery.html")
    print(f"Mock mode: {mock_state} via {MOCK_ENV}=1")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping PowerClub Val demo harness.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
