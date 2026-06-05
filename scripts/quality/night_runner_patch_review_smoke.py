#!/usr/bin/env python3
from __future__ import annotations

import py_compile
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "diagnostics" / "night_runner_patch_review.py"
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


def test_review_compiles_and_runs() -> str:
    assert_true(SCRIPT.exists(), "patch review script exists")
    py_compile.compile(str(SCRIPT), doraise=True)
    proc = _run(["python3", str(SCRIPT)])
    if proc.returncode != 0:
        raise AssertionError(f"patch review failed: {proc.stderr.strip()}")
    return proc.stdout


def test_review_output(output: str) -> None:
    assert_contains(output, "Night Runner Patch Review", "title")
    assert_contains(output, "Sleep Mode Ladder", "NR15 result")
    assert_contains(output, "reported patch guard", "reported patch guard result")
    assert_contains(output, "no runtime", "no runtime statement")
    assert_contains(output, "CLIENT_GROCERY.md", "grocery protected status")
    assert_contains(output, "CLIENT_FOLDERS.json", "folders protected status")
    assert_contains(output, "NIGHT-RUNNER-17", "next lane")
    assert_contains(output, "live client file contents read: no", "live content guard")
    assert_contains(output, "auth.json/config.toml contents printed: no", "secret guard")
    for marker in FORBIDDEN_OUTPUT_MARKERS:
        assert_not_contains(output, marker, "secret-like output marker")


def test_protected_live_files_not_staged() -> None:
    staged = set(_git_cached_names())
    for path in PROTECTED_FILES:
        assert_true(path not in staged, f"{path} is not staged")


def main() -> None:
    output = test_review_compiles_and_runs()
    test_review_output(output)
    test_protected_live_files_not_staged()
    print("PASS night_runner_patch_review_smoke")


if __name__ == "__main__":
    main()
