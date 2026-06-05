#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.case_timeline_events import (  # noqa: E402
    CASE_ID,
    CaseTimelineEventSqliteStore,
    is_live_timeline_sqlite_enabled,
    parse_case_timeline_event_draft,
)
from scripts.diagnostics.caso_finca_timeline_sqlite_export import build_report  # noqa: E402


KAREN_CLIENT_ID = "karen"
REQUIRED_TABLES = {
    "case_timeline_events",
    "case_timeline_event_audit",
}
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


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _sqlite_names(db_path: Path, *, kind: str) -> set[str]:
    with sqlite3.connect(str(db_path)) as conn:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type = ?", (kind,)).fetchall()
    return {str(row[0]) for row in rows}


def _table_columns(db_path: Path, table: str) -> set[str]:
    with sqlite3.connect(str(db_path)) as conn:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {str(row[1]) for row in rows}


def run_dry_run(db_path: str | Path, *, client_id: str = KAREN_CLIENT_ID, case_id: str = CASE_ID) -> dict[str, object]:
    path = Path(db_path)
    store = CaseTimelineEventSqliteStore(path)

    store.initialize_schema()
    store.initialize_schema()

    tables = store.schema_tables()
    indexes = _sqlite_names(path, kind="index")
    missing_tables = sorted(REQUIRED_TABLES - tables)
    missing_indexes = sorted(REQUIRED_INDEXES - indexes)
    missing_columns = {
        table: sorted(required - _table_columns(path, table))
        for table, required in REQUIRED_COLUMNS.items()
        if table in tables and required - _table_columns(path, table)
    }

    if missing_tables or missing_indexes or missing_columns:
        raise RuntimeError(
            "Timeline SQLite dry-run schema verification failed: "
            + json.dumps(
                {
                    "missing_tables": missing_tables,
                    "missing_indexes": missing_indexes,
                    "missing_columns": missing_columns,
                },
                sort_keys=True,
            )
        )

    draft = parse_case_timeline_event_draft(
        "Val, anota en Caso Finca que el 12 de mayo de 2024 recibimos respuesta del juzgado"
    )
    if draft is None:
        raise RuntimeError("Timeline migration dry-run could not build test draft")

    record = store.insert_from_draft(draft, client_id=client_id, case_id=case_id, now="2026-06-04T23:55:00+00:00")
    records = store.list_events(client_id=client_id, case_id=case_id)
    audit_rows = store.audit_rows(event_id=record.event_id)
    export_report = build_report(path, client_id=client_id, case_id=case_id)

    return {
        "db_path": str(path),
        "generated_at": _now_iso(),
        "tables": sorted(tables),
        "indexes": sorted(indexes & REQUIRED_INDEXES),
        "columns_verified": {table: sorted(columns) for table, columns in REQUIRED_COLUMNS.items()},
        "inserted_event_count": len(records),
        "audit_rows_for_test_event": len(audit_rows),
        "export_report_ok": "# Caso Finca Timeline SQLite Export" in export_report
        and "Audit rows: 1" in export_report
        and record.event_id not in export_report,
        "live_enabled": is_live_timeline_sqlite_enabled(),
    }


def render_report(result: dict[str, object]) -> str:
    lines = [
        "# Caso Finca Timeline SQLite Migration Dry-Run",
        "",
        f"DB path: {result['db_path']}",
        f"generated_at: {result['generated_at']}",
        "",
        "Decision: PASS_DRY_RUN",
        "Scope: temp SQLite DB only; production DB and Telegram live persistence were not touched.",
        "",
        "Schema:",
        f"- tables: {', '.join(result['tables'])}",
        f"- required indexes: {', '.join(result['indexes'])}",
        "- required columns: verified",
        "",
        "Usability proof:",
        f"- inserted event count: {result['inserted_event_count']}",
        f"- audit rows for test event: {result['audit_rows_for_test_event']}",
        f"- export diagnostic works: {result['export_report_ok']}",
        "",
        f"Live timeline SQLite enabled: {result['live_enabled']}",
        "",
        "Safety notes:",
        "- Non-/tmp paths are refused by the temp SQLite adapter.",
        "- This dry-run does not enable feature flags.",
        "- This dry-run does not write real Val0 memory DBs or live Karen client files.",
    ]
    return "\n".join(lines).strip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Apply and verify the Caso Finca timeline SQLite schema against an explicit temp DB path."
    )
    parser.add_argument("--db-path", required=True, help="Required temp SQLite DB path. Non-/tmp paths are refused.")
    parser.add_argument("--client-id", default=KAREN_CLIENT_ID, help="Client ID for the inserted dry-run record.")
    parser.add_argument("--case-id", default=CASE_ID, help="Case ID for the inserted dry-run record.")
    args = parser.parse_args(argv)

    try:
        result = run_dry_run(args.db_path, client_id=str(args.client_id).strip(), case_id=str(args.case_id).strip())
    except Exception as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2

    print(render_report(result), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
