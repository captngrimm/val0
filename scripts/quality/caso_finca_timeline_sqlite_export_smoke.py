#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.case_timeline_events import (  # noqa: E402
    CASE_ID,
    CaseTimelineEventSqliteStore,
    parse_case_timeline_event_draft,
)


KAREN_CLIENT_ID = "kar" + "en"
OTHER_CLIENT_ID = "other-client"
OTHER_CASE_ID = "CASE:OTHER-001"
LIVE_GROCERY = ROOT / "clients" / KAREN_CLIENT_ID / "CLIENT_GROCERY.md"
LIVE_FOLDERS = ROOT / "clients" / KAREN_CLIENT_ID / "CLIENT_FOLDERS.json"
SCRIPT = ROOT / "scripts" / "diagnostics" / "caso_finca_timeline_sqlite_export.py"
FORBIDDEN_OUTPUT = ("event:", "vfms:", "ID técnico", "audit:", "source_ref", "source_type")


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() not in text.lower():
        raise AssertionError(f"{label}: missing {needle!r} in {text!r}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() in text.lower():
        raise AssertionError(f"{label}: unexpected {needle!r} in {text!r}")


def _draft(text: str):
    draft = parse_case_timeline_event_draft(text)
    assert_true(draft is not None, f"draft parsed: {text}")
    return draft


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(SCRIPT), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def _assert_safe_report(output: str, *, label: str) -> None:
    assert_contains(output, "# Caso Finca Timeline SQLite Export", f"{label} header")
    assert_contains(output, "WARNING: temp/fixture SQLite diagnostic only", f"{label} temp warning")
    assert_contains(output, "## Timeline", f"{label} timeline heading")
    assert_contains(output, "## Audit Summary", f"{label} audit heading")
    assert_contains(output, "## Safety Notes", f"{label} safety heading")
    assert_contains(output, "Nora/la abogada confirms legal effect", f"{label} safety note")
    for needle in FORBIDDEN_OUTPUT:
        assert_not_contains(output, needle, f"{label} avoids internal output {needle}")


def test_export_refusals() -> None:
    missing = _run([])
    assert_true(missing.returncode != 0, "missing db path refused")
    assert_contains(missing.stderr, "--db-path", "missing db path usage")

    non_tmp = _run(["--db-path", str(ROOT / "val0_memory.enc.db"), "--client-id", KAREN_CLIENT_ID, "--case-id", "caso_finca"])
    assert_true(non_tmp.returncode == 2, "non-/tmp DB path refused")
    assert_contains(non_tmp.stderr, "outside temp directory", "non-/tmp refusal reason")


def test_export_timeline_audit_and_live_file_safety() -> None:
    before_grocery = LIVE_GROCERY.read_text(encoding="utf-8") if LIVE_GROCERY.exists() else None
    before_folders = LIVE_FOLDERS.read_text(encoding="utf-8") if LIVE_FOLDERS.exists() else None

    with tempfile.TemporaryDirectory(prefix="val0_case_timeline_export_") as tmp:
        db_path = Path(tmp) / "case_timeline_events.sqlite3"
        store = CaseTimelineEventSqliteStore(db_path)
        exact = store.insert_from_draft(
            _draft("Val, anota en Caso Finca que el 12 de mayo de 2024 recibimos respuesta del juzgado"),
            client_id=KAREN_CLIENT_ID,
            now="2026-06-04T23:31:00+00:00",
        )
        year = store.insert_from_draft(
            _draft("Val, registra en Caso Finca que en 2021 se presentó una solicitud al Registro Público"),
            client_id=KAREN_CLIENT_ID,
            now="2026-06-04T23:32:00+00:00",
        )
        unknown = store.insert_from_draft(
            _draft("Val, agrega a la línea de tiempo que falta confirmar la fecha del oficio"),
            client_id=KAREN_CLIENT_ID,
            now="2026-06-04T23:33:00+00:00",
        )
        other = store.insert_from_draft(
            _draft("Val, registra en Caso Finca que en 2022 pasó algo de otro cliente"),
            client_id=OTHER_CLIENT_ID,
            case_id=OTHER_CASE_ID,
            now="2026-06-04T23:34:00+00:00",
        )
        deleted = store.soft_delete(
            exact.event_id,
            client_id=KAREN_CLIENT_ID,
            case_id=CASE_ID,
            actor="smoke",
            reason="export smoke soft-delete",
            now="2026-06-04T23:35:00+00:00",
        )
        assert_true(deleted is not None, "deleted event prepared")

        default = _run(["--db-path", str(db_path), "--client-id", KAREN_CLIENT_ID, "--case-id", "caso_finca"])
        assert_true(default.returncode == 0, f"default export passes: {default.stderr}")
        output = default.stdout
        _assert_safe_report(output, label="default export")
        assert_contains(output, "client_id: karen", "client id header")
        assert_contains(output, f"case_id: {CASE_ID}", "case id header")
        assert_contains(output, "2021 (solo año)", "year-only event")
        assert_contains(output, "Fecha pendiente", "unknown bucket")
        assert_contains(output, "fecha pendiente", "unknown label")
        assert_contains(output, "Audit rows: 4", "audit rows filtered to Karen/Caso Finca")
        assert_contains(output, "created_from_draft", "audit latest actions include create")
        assert_contains(output, "soft_deleted", "audit latest actions include delete")
        assert_not_contains(output, exact.title, "deleted hidden by default")
        assert_not_contains(output, other.title, "other client hidden")
        assert_true(output.find("2021 (solo año)") < output.find("Fecha pendiente"), "known dates before unknown bucket")

        with_deleted = _run(
            ["--db-path", str(db_path), "--client-id", KAREN_CLIENT_ID, "--case-id", "caso_finca", "--include-deleted"]
        )
        assert_true(with_deleted.returncode == 0, f"include-deleted export passes: {with_deleted.stderr}")
        deleted_output = with_deleted.stdout
        _assert_safe_report(deleted_output, label="include-deleted export")
        assert_contains(deleted_output, "Eliminados / ocultos", "deleted section shown")
        assert_contains(deleted_output, exact.title, "deleted event shown with include-deleted")
        assert_not_contains(deleted_output, other.title, "other client still hidden with include-deleted")

        wrong_case = _run(["--db-path", str(db_path), "--client-id", KAREN_CLIENT_ID, "--case-id", OTHER_CASE_ID])
        assert_true(wrong_case.returncode == 0, "wrong case export runs")
        assert_contains(wrong_case.stdout, "Todavía no hay eventos", "wrong case no event copy")
        assert_not_contains(wrong_case.stdout, year.title, "wrong case does not leak Karen event")

    after_grocery = LIVE_GROCERY.read_text(encoding="utf-8") if LIVE_GROCERY.exists() else None
    after_folders = LIVE_FOLDERS.read_text(encoding="utf-8") if LIVE_FOLDERS.exists() else None
    assert_true(before_grocery == after_grocery, "CLIENT_GROCERY.md untouched")
    assert_true(before_folders == after_folders, "CLIENT_FOLDERS.json untouched")


def main() -> None:
    test_export_refusals()
    test_export_timeline_audit_and_live_file_safety()
    print("PASS caso_finca_timeline_sqlite_export_smoke")


if __name__ == "__main__":
    main()
