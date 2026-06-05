#!/usr/bin/env python3
from __future__ import annotations

import py_compile
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "diagnostics" / "night_runner_overnight_candidate_summary.py"
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
    assert_true(SCRIPT.exists(), "overnight candidate summary script exists")
    py_compile.compile(str(SCRIPT), doraise=True)
    proc = _run(["python3", str(SCRIPT)])
    if proc.returncode != 0:
        raise AssertionError(f"diagnostic failed: {proc.stderr.strip()}")
    return proc.stdout


def test_summary_output(output: str) -> None:
    for needle in (
        "Night Runner Overnight Candidate Summary",
        "bedtime workflow packet",
        "manual overnight trial",
        "manual overnight report",
        "CLIENT_GROCERY.md",
        "CLIENT_FOLDERS.json",
        "dirty-unstaged",
        "bot.py",
        "core",
        "NIGHT-RUNNER-22",
        "non-runtime overnight candidates only",
        "live client file contents read: no",
        "auth.json/config.toml contents printed: no",
        "protected live client contents printed: no",
    ):
        assert_contains(output, needle, f"summary contains {needle}")
    for marker in FORBIDDEN_OUTPUT_MARKERS:
        assert_not_contains(output, marker, "secret marker")


def test_protected_live_files_not_staged() -> None:
    staged = set(_git_cached_names())
    for path in PROTECTED_FILES:
        assert_true(path not in staged, f"{path} is not staged")
    assert_true(not staged, "no staged files remain")


def main() -> None:
    output = test_diagnostic_compiles_and_runs()
    test_summary_output(output)
    test_protected_live_files_not_staged()
    print("PASS night_runner_overnight_candidate_summary_smoke")


if __name__ == "__main__":
    main()
