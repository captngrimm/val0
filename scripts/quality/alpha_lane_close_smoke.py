#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "ops" / "alpha_lane_close.py"
SOURCE_BENCHMARK = ROOT / "docs" / "ops" / "VAL0_ALPHA_BENCHMARK_LOG.md"
LIVE_GROCERY = ROOT / "clients" / "karen" / "CLIENT_GROCERY.md"


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle in text:
        raise AssertionError(f"{label}: unexpected {needle!r}")


def _run(args: list[str], *, expect: int = 0) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != expect:
        raise AssertionError(
            f"expected exit {expect}, got {proc.returncode}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    return proc


def _base_args(path: Path, *, notes: str = "Fake note") -> list[str]:
    return [
        "--benchmark-path", str(path),
        "--id", "A-999",
        "--lane", "Fake Lane",
        "--estimate", "1 h",
        "--start", "2026-06-03 18:00",
        "--end", "2026-06-03 18:10",
        "--actual", "10 min",
        "--commit", "abc1234",
        "--status", "PASS",
        "--notes", notes,
    ]


def main() -> int:
    assert_true(SCRIPT.exists(), "alpha lane close helper exists")
    before_grocery = LIVE_GROCERY.read_text(encoding="utf-8") if LIVE_GROCERY.exists() else None

    with tempfile.TemporaryDirectory(prefix="alpha_lane_close_") as tmp:
        temp_benchmark = Path(tmp) / "VAL0_ALPHA_BENCHMARK_LOG.md"
        temp_benchmark.write_text(SOURCE_BENCHMARK.read_text(encoding="utf-8"), encoding="utf-8")

        before = temp_benchmark.read_text(encoding="utf-8")
        dry = _run([*_base_args(temp_benchmark), "--dry-run"])
        after_dry = temp_benchmark.read_text(encoding="utf-8")
        assert_true(before == after_dry, "dry-run does not write")
        assert_contains(dry.stdout, "DRY RUN", "dry-run output marker")
        assert_contains(dry.stdout, "| A-999 | Fake Lane |", "dry-run prints proposed row")
        assert_not_contains(dry.stdout, "stage", "dry-run does not mention staging")
        assert_not_contains(dry.stdout, "CLIENT_GROCERY.md", "dry-run does not mention live data file")

        add = _run(_base_args(temp_benchmark))
        assert_contains(add.stdout, "OK: inserted lane A-999", "insert output")
        assert_not_contains(add.stdout, "CLIENT_GROCERY.md", "write output does not mention live data file")
        written = temp_benchmark.read_text(encoding="utf-8")
        assert_contains(written, "| A-999 | Fake Lane | 1 h | 2026-06-03 18:00 | 2026-06-03 18:10 | 10 min | `abc1234` | PASS | Fake note |", "inserted row")

        dup = _run(_base_args(temp_benchmark), expect=1)
        assert_contains(dup.stderr + dup.stdout, "already exists", "duplicate rejected")

        replace = _run([*_base_args(temp_benchmark, notes="Replacement note"), "--replace"])
        assert_contains(replace.stdout, "OK: replaced lane A-999", "replace output")
        replaced = temp_benchmark.read_text(encoding="utf-8")
        assert_contains(replaced, "Replacement note", "replacement wrote new note")
        assert_not_contains(replaced, "| A-999 | Fake Lane | 1 h | 2026-06-03 18:00 | 2026-06-03 18:10 | 10 min | `abc1234` | PASS | Fake note |", "old row replaced")

        note_args = [
            *_base_args(temp_benchmark, notes="Replacement note"),
            "--replace",
            "--next-note",
            "A-999 is a fake smoke lane.",
            "--planned-name",
            "Fixture Migration v2",
            "--planned-status",
            "WATCH",
        ]
        _run(note_args)
        updated = temp_benchmark.read_text(encoding="utf-8")
        assert_contains(updated, "A-999 is a fake smoke lane.", "next note updated")
        assert_contains(updated, "| 6 | Fixture Migration v2 | 3-5 h | WATCH |", "planned status updated")

    after_grocery = LIVE_GROCERY.read_text(encoding="utf-8") if LIVE_GROCERY.exists() else None
    assert_true(before_grocery == after_grocery, "CLIENT_GROCERY.md untouched by smoke")
    print("PASS: Alpha lane close helper smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
