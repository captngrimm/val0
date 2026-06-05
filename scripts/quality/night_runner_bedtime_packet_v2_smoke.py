#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "ops" / "NIGHT_RUNNER_BEDTIME_WORKFLOW_V2.md"
PACKET = ROOT / "docs" / "ops" / "night_runner_bedtime_packet_v2.yaml"
PROTECTED_FILES = (
    "clients/karen/CLIENT_GROCERY.md",
    "clients/karen/CLIENT_FOLDERS.json",
)
ALLOWED_TESTS = {
    "python3 scripts/quality/night_runner_readiness_summary_smoke.py",
    "python3 scripts/quality/night_runner_patch_review_smoke.py",
    "python3 scripts/quality/night_runner_tiny_task_execution_guard_smoke.py",
    "python3 scripts/quality/client_isolation_audit.py",
    "git diff --check",
}
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


def assert_equal(left, right, label: str) -> None:
    if left != right:
        raise AssertionError(f"{label}: expected {right!r}, got {left!r}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle in text:
        raise AssertionError(f"{label}: unexpected {needle!r}")


def _parse_scalar(value: str):
    value = value.strip()
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value in {"null", "None", "~"}:
        return None
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def _parse_simple_yaml(path: Path) -> dict:
    data: dict = {}
    current_key: str | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- "):
            if current_key is None:
                raise AssertionError("YAML list item without key")
            data.setdefault(current_key, []).append(_parse_scalar(stripped[2:]))
            continue
        if ":" not in stripped:
            raise AssertionError(f"Unsupported YAML line: {raw_line!r}")
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value:
            data[key] = _parse_scalar(value)
            current_key = None
        else:
            data[key] = []
            current_key = key
    return data


def _git_cached_names() -> list[str]:
    proc = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(f"git cached diff failed: {proc.stderr.strip()}")
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def test_doc() -> None:
    assert_true(DOC.exists(), "workflow doc exists")
    text = DOC.read_text(encoding="utf-8")
    assert_contains(text, "Bedtime Workflow v2", "title")
    assert_contains(text, "morning report", "morning report")
    assert_contains(text, "approve", "approve decision")
    assert_contains(text, "discard", "discard decision")
    assert_contains(text, "continue", "continue decision")
    assert_contains(text, "CLIENT_GROCERY.md", "grocery protected file")
    assert_contains(text, "CLIENT_FOLDERS.json", "folders protected file")
    assert_contains(text, "runtime bot/core work is forbidden", "runtime forbidden")
    for marker in FORBIDDEN_OUTPUT_MARKERS:
        assert_not_contains(text, marker, "secret-like doc marker")


def test_packet() -> None:
    assert_true(PACKET.exists(), "packet exists")
    packet = _parse_simple_yaml(PACKET)
    assert_equal(packet.get("allow_file_edits"), False, "allow_file_edits false")
    assert_equal(packet.get("allow_commit"), False, "allow_commit false")
    assert_equal(packet.get("allow_restart"), False, "allow_restart false")
    assert_equal(packet.get("allow_live_writes"), False, "allow_live_writes false")
    report_path = str(packet.get("report_path", ""))
    assert_true(report_path.startswith("tmp/night_runner/"), "report path under tmp/night_runner")
    forbidden = set(packet.get("forbidden_files", []))
    assert_true("clients/karen/CLIENT_GROCERY.md" in forbidden, "grocery forbidden")
    assert_true("clients/karen/CLIENT_FOLDERS.json" in forbidden, "folders forbidden")
    assert_true("bot.py" in forbidden, "bot.py forbidden")
    assert_true("core/**" in forbidden, "core forbidden")
    tests = set(packet.get("tests_to_run", []))
    assert_true(bool(tests), "tests present")
    for command in tests:
        assert_true(command in ALLOWED_TESTS, f"safe diagnostic allowlist: {command}")


def test_protected_live_files_not_staged() -> None:
    staged = set(_git_cached_names())
    for path in PROTECTED_FILES:
        assert_true(path not in staged, f"{path} is not staged")


def main() -> None:
    test_doc()
    test_packet()
    test_protected_live_files_not_staged()
    print("PASS night_runner_bedtime_packet_v2_smoke")


if __name__ == "__main__":
    main()
