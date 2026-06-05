#!/usr/bin/env python3
from __future__ import annotations

import py_compile
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "diagnostics" / "night_runner_readiness_summary.py"
PROTECTED_FILES = (
    "clients/karen/CLIENT_GROCERY.md",
    "clients/karen/CLIENT_FOLDERS.json",
)
FORBIDDEN_OUTPUT_MARKERS = (
    "refresh_token",
    "access_token",
    "id_token",
    "client_secret",
    "sk-",
)


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle in text:
        raise AssertionError(f"{label}: unexpected {needle!r}")


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _git_cached_names() -> list[str]:
    proc = _run(["git", "diff", "--cached", "--name-only"])
    if proc.returncode != 0:
        raise AssertionError(f"git cached diff failed: {proc.stderr.strip()}")
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def test_diagnostic_compiles_and_runs() -> str:
    assert_true(SCRIPT.exists(), "readiness summary script exists")
    py_compile.compile(str(SCRIPT), doraise=True)
    proc = _run(["python3", str(SCRIPT)])
    if proc.returncode != 0:
        raise AssertionError(f"diagnostic failed: {proc.stderr.strip()}")
    return proc.stdout


def test_summary_output(output: str) -> None:
    assert_contains(output, "Night Runner Readiness Summary", "summary title")
    assert_contains(output, "Codex bridge discovery", "Codex bridge discovery section")
    assert_contains(output, "No-op invocation", "no-op invocation section")
    assert_contains(output, "Read-only planning", "read-only planning section")
    assert_contains(output, "Docs diagnostic smoke", "docs diagnostic smoke section")
    assert_contains(output, "Sleep Mode Ladder", "sleep mode ladder section")
    assert_contains(output, "Tiny task dry-run", "tiny task dry-run ladder item")
    assert_contains(output, "Reported patch guard", "reported patch guard ladder item")
    assert_contains(output, "Next", "next ladder item")
    assert_contains(output, "live client file contents read: no", "live content guard")
    assert_contains(output, "auth.json/config.toml contents printed: no", "secret content guard")
    assert_contains(output, "NIGHT-RUNNER-16", "recommended next lane")
    for path in PROTECTED_FILES:
        assert_contains(output, path, f"{path} status mention")
    for marker in FORBIDDEN_OUTPUT_MARKERS:
        assert_not_contains(output, marker, "secret-like output marker")


def test_protected_live_files_not_staged() -> None:
    staged = set(_git_cached_names())
    for path in PROTECTED_FILES:
        assert_true(path not in staged, f"{path} is not staged")


def main() -> None:
    output = test_diagnostic_compiles_and_runs()
    test_summary_output(output)
    test_protected_live_files_not_staged()
    print("PASS night_runner_readiness_summary_smoke")


if __name__ == "__main__":
    main()
