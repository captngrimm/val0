#!/usr/bin/env python3
from __future__ import annotations

import os
import stat
import subprocess
import tempfile
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


SCRIPT = ROOT / "scripts" / "ops" / "night_runner_codex_bridge_discovery.py"
KAREN_CLIENT_ID = "kar" + "en"
LIVE_GROCERY = ROOT / "clients" / KAREN_CLIENT_ID / "CLIENT_GROCERY.md"
LIVE_FOLDERS = ROOT / "clients" / KAREN_CLIENT_ID / "CLIENT_FOLDERS.json"
SECRET_SENTINELS = ("SUPER_SECRET_TOKEN", "sk-test-secret", "refresh_token")


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r} in {text!r}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle in text:
        raise AssertionError(f"{label}: unexpected {needle!r} in {text!r}")


def _read_live_file(path: Path) -> str | None:
    return path.read_text(encoding="utf-8") if path.exists() else None


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(SCRIPT), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def _write_fake_codex_binary(path_dir: Path) -> None:
    binary = path_dir / "codex"
    binary.write_text("#!/bin/sh\nprintf 'fake codex\\n'\n", encoding="utf-8")
    binary.chmod(binary.stat().st_mode | stat.S_IXUSR)


def _assert_common_report_shape(output: str) -> None:
    assert_contains(output, "Night Runner Codex Bridge Discovery", "report header")
    assert_contains(output, "Decision:", "decision")
    assert_contains(output, "secret contents printed: no", "secret safety")
    assert_contains(output, "Night Runner files:", "night runner files")
    assert_contains(output, "scripts/ops/night_runner_dry_run.py: present", "night runner script detected")
    assert_contains(output, "docs/ops/NIGHT_RUNNER_BEDTIME_WORKFLOW.md: present", "bedtime workflow detected")
    assert_contains(output, "Protected live files:", "protected files section")
    assert_contains(output, "clients/karen/CLIENT_GROCERY.md", "grocery status reported")
    assert_contains(output, "clients/karen/CLIENT_FOLDERS.json", "folders status reported")
    assert_contains(output, "Next recommended safe path:", "next path")
    assert_contains(output, "This script did not run Codex on a task.", "no task execution")
    for sentinel in SECRET_SENTINELS:
        assert_not_contains(output, sentinel, f"secret sentinel hidden: {sentinel}")


def test_config_present_but_binary_missing_and_secrets_hidden() -> None:
    with tempfile.TemporaryDirectory(prefix="val0_codex_bridge_config_only_") as tmp:
        codex_home = Path(tmp) / ".codex"
        codex_home.mkdir()
        (codex_home / "auth.json").write_text('{"token":"SUPER_SECRET_TOKEN","refresh_token":"refresh_token"}', encoding="utf-8")
        (codex_home / "config.toml").write_text('api_key = "sk-test-secret"\n', encoding="utf-8")
        proc = _run("--codex-home", str(codex_home), "--path-search", "", "--ignore-common-locations")
        assert_true(proc.returncode == 0, "config-present run exits 0")
        output = proc.stdout
        _assert_common_report_shape(output)
        assert_contains(output, "Decision: CODEX_CONFIG_PRESENT_BUT_BIN_MISSING", "config present missing binary decision")
        assert_contains(output, "codex binary available: no", "binary missing")
        assert_contains(output, "auth.json present: yes", "auth present")
        assert_contains(output, "config.toml present: yes", "config present")


def test_missing_codex_home_reports_not_configured() -> None:
    with tempfile.TemporaryDirectory(prefix="val0_codex_bridge_missing_home_") as tmp:
        missing_home = Path(tmp) / "missing-codex"
        proc = _run("--codex-home", str(missing_home), "--path-search", "", "--ignore-common-locations")
        assert_true(proc.returncode == 0, "missing-home run exits 0")
        output = proc.stdout
        _assert_common_report_shape(output)
        assert_contains(output, "Decision: CODEX_NOT_CONFIGURED", "missing home decision")
        assert_contains(output, "~/.codex directory present: no", "home missing")


def test_local_ready_with_fake_binary_and_config() -> None:
    with tempfile.TemporaryDirectory(prefix="val0_codex_bridge_ready_") as tmp:
        root = Path(tmp)
        codex_home = root / ".codex"
        bin_dir = root / "bin"
        codex_home.mkdir()
        bin_dir.mkdir()
        (codex_home / "config.toml").write_text("# fake config only\n", encoding="utf-8")
        _write_fake_codex_binary(bin_dir)
        proc = _run("--codex-home", str(codex_home), "--path-search", str(bin_dir), "--ignore-common-locations")
        assert_true(proc.returncode == 0, "fake-ready run exits 0")
        output = proc.stdout
        _assert_common_report_shape(output)
        assert_contains(output, "Decision: CODEX_LOCAL_READY", "local ready decision")
        assert_contains(output, "codex binary available: yes", "binary found")
        assert_contains(output, str(bin_dir / "codex"), "fake binary path shown")


def test_live_files_untouched_by_discovery() -> None:
    before_grocery = _read_live_file(LIVE_GROCERY)
    before_folders = _read_live_file(LIVE_FOLDERS)
    proc = _run()
    assert_true(proc.returncode == 0, "real discovery exits 0")
    _assert_common_report_shape(proc.stdout)
    after_grocery = _read_live_file(LIVE_GROCERY)
    after_folders = _read_live_file(LIVE_FOLDERS)
    assert_true(before_grocery == after_grocery, "CLIENT_GROCERY.md untouched")
    assert_true(before_folders == after_folders, "CLIENT_FOLDERS.json untouched")


def main() -> None:
    test_config_present_but_binary_missing_and_secrets_hidden()
    test_missing_codex_home_reports_not_configured()
    test_local_ready_with_fake_binary_and_config()
    test_live_files_untouched_by_discovery()
    print("PASS night_runner_codex_bridge_discovery_smoke")


if __name__ == "__main__":
    main()
