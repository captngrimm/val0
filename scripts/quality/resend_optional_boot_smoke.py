#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() in text.lower():
        raise AssertionError(f"{label}: unexpected {needle!r} in output")


def test_bot_import_without_resend_key() -> None:
    env = os.environ.copy()
    env.pop("RESEND_API_KEY", None)
    code = (
        "import bot\n"
        "assert bot.RESEND_EMAIL_ENABLED is False\n"
        "try:\n"
        "    bot.send_email_resend('nobody@example.com', 'Smoke', 'Body')\n"
        "except RuntimeError as exc:\n"
        "    assert str(exc) == bot.EMAIL_NOT_CONFIGURED_MESSAGE\n"
        "else:\n"
        "    raise AssertionError('send_email_resend did not refuse missing config')\n"
        "print('RESEND_OPTIONAL_BOOT_OK')\n"
    )
    proc = subprocess.run(
        ["./scripts/val0py", "-c", code],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )
    output = proc.stdout + proc.stderr
    assert_true("RESEND_OPTIONAL_BOOT_OK" in proc.stdout, "bot imports and refuses email without Resend key")
    assert_not_contains(output, "Missing RESEND_API_KEY", "old startup crash is gone")
    assert_not_contains(output, "Bearer ", "no bearer token printed")


def main() -> int:
    test_bot_import_without_resend_key()
    print("PASS: Resend optional boot smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
