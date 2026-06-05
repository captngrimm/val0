#!/usr/bin/env python3
from __future__ import annotations

import sqlite3
import subprocess
import tempfile
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.case_timeline_events import (  # noqa: E402
    CASE_ID,
    CaseTimelineEventSqliteStore,
    is_live_timeline_sqlite_enabled,
)


KAREN_CLIENT_ID = "kar" + "en"
LIVE_GROCERY = ROOT / "clients" / KAREN_CLIENT_ID / "CLIENT_GROCERY.md"
LIVE_FOLDERS = ROOT / "clients" / KAREN_CLIENT_ID / "CLIENT_FOLDERS.json"
SCRIPT = ROOT / "scripts" / "ops" / "caso_finca_timeline_sqlite_migration_dry_run.py"
EXPORT_SCRIPT = ROOT / "scripts" / "diagnostics" / "caso_finca_timeline_sqlite_export.py"
REQUIRED_TABLES = {"case_timeline_events", "case_timeline_event_audit"}
REQUIRED_INDEXES = {
    "idx_case_timeline_events_client_case",
    "idx_case_timeline_events_date",
    "idx_case_timeline_event_audit_event",
}
REQUIRED_COLUMNS = {
    "case_timeline_events": {
        "event_id",
        "client_id",
        "case_id",
        "title",
        "description",
        "event_date",
        "event_date_precision",
        "recorded_at",
        "source_type",
        "source_ref",
        "confirmation_status",
        "confidence",
        "legal_effect_status",
        "created_by",
        "created_at",
        "updated_at",
        "deleted_at",
    },
    "case_timeline_event_audit": {
        "audit_id",
        "event_id",
        "client_id",
        "case_id",
        "action",
        "actor",
        "timestamp",
        "before_json",
        "after_json",
        "reason",
    },
}


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() not in text.lower():
        raise AssertionError(f"{label}: missing {needle!r} in {text!r}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() in text.lower():
        raise AssertionError(f"{label}: unexpected {needle!r} in {text!r}")


def _read_live_file(path: Path) -> str | None:
    return path.read_text(encoding="utf-8") if path.exists() else None


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(SCRIPT), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def _run_export(db_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "python3",
            str(EXPORT_SCRIPT),
            "--db-path",
            str(db_path),
            "--client-id",
            KAREN_CLIENT_ID,
            "--case-id",
            "caso_finca",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def _sqlite_names(db_path: Path, *, kind: str) -> set[str]:
    with sqlite3.connect(str(db_path)) as conn:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type = ?", (kind,)).fetchall()
    return {str(row[0]) for row in rows}


def _table_columns(db_path: Path, table: str) -> set[str]:
    with sqlite3.connect(str(db_path)) as conn:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {str(row[1]) for row in rows}


def test_dry_run_refusals() -> None:
    missing = _run([])
    assert_true(missing.returncode != 0, "missing db path refused")
    assert_contains(missing.stderr, "--db-path", "missing db path usage")

    non_tmp = _run(["--db-path", str(ROOT / "val0_memory.enc.db")])
    assert_true(non_tmp.returncode == 2, "non-/tmp DB path refused")
    assert_contains(non_tmp.stderr, "outside temp directory", "non-/tmp refusal reason")


def test_temp_migration_idempotent_schema_usable_export_and_live_safety() -> None:
    before_grocery = _read_live_file(LIVE_GROCERY)
    before_folders = _read_live_file(LIVE_FOLDERS)

    with tempfile.TemporaryDirectory(prefix="val0_case_timeline_migration_dry_run_") as tmp:
        db_path = Path(tmp) / "case_timeline_events.sqlite3"

        first = _run(["--db-path", str(db_path), "--client-id", KAREN_CLIENT_ID, "--case-id", CASE_ID])
        assert_true(first.returncode == 0, f"first migration dry-run passes: {first.stderr}")
        assert_contains(first.stdout, "PASS_DRY_RUN", "first run PASS")
        assert_contains(first.stdout, "required columns: verified", "columns verified")
        assert_contains(first.stdout, "export diagnostic works: True", "export proof")
        assert_contains(first.stdout, "Live timeline SQLite enabled: False", "live guard false")

        second = _run(["--db-path", str(db_path), "--client-id", KAREN_CLIENT_ID, "--case-id", CASE_ID])
        assert_true(second.returncode == 0, f"second migration dry-run passes: {second.stderr}")
        assert_contains(second.stdout, "PASS_DRY_RUN", "second run PASS")

        tables = _sqlite_names(db_path, kind="table")
        indexes = _sqlite_names(db_path, kind="index")
        assert_true(REQUIRED_TABLES <= tables, "required tables exist")
        assert_true(REQUIRED_INDEXES <= indexes, "required indexes exist")
        for table, columns in REQUIRED_COLUMNS.items():
            assert_true(columns <= _table_columns(db_path, table), f"required columns exist for {table}")

        store = CaseTimelineEventSqliteStore(db_path)
        records = store.list_events(client_id=KAREN_CLIENT_ID, case_id=CASE_ID)
        assert_true(len(records) == 2, "adapter inserted one event per idempotent dry-run")
        audit = store.audit_rows()
        assert_true(len(audit) == 2, "audit row exists after each insert")
        assert_true(all(row["action"] == "created_from_draft" for row in audit), "audit actions recorded")

        export = _run_export(db_path)
        assert_true(export.returncode == 0, f"export diagnostic works after migration: {export.stderr}")
        assert_contains(export.stdout, "# Caso Finca Timeline SQLite Export", "export header")
        assert_contains(export.stdout, "Audit rows: 2", "export audit count")
        assert_not_contains(export.stdout, "event:", "export does not leak internal event IDs")

    assert_true(not is_live_timeline_sqlite_enabled(), "live guard remains disabled")
    assert_true(_read_live_file(LIVE_GROCERY) == before_grocery, "CLIENT_GROCERY.md untouched")
    assert_true(_read_live_file(LIVE_FOLDERS) == before_folders, "CLIENT_FOLDERS.json untouched")


def main() -> None:
    test_dry_run_refusals()
    test_temp_migration_idempotent_schema_usable_export_and_live_safety()
    print("PASS caso_finca_timeline_sqlite_migration_dry_run_smoke")


if __name__ == "__main__":
    main()
