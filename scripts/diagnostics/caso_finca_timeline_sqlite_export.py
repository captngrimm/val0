#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.case_timeline_events import (  # noqa: E402
    CASE_ID,
    CaseTimelineEventSqliteStore,
    render_sqlite_timeline_events_for_user,
)


CASE_ALIASES = {
    "caso_finca": CASE_ID,
    "caso-finca": CASE_ID,
    "finca": CASE_ID,
    CASE_ID: CASE_ID,
}


def _case_id(value: str) -> str:
    clean = str(value or "").strip()
    return CASE_ALIASES.get(clean, clean)


def _generated_at() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_report(db_path: str | Path, *, client_id: str, case_id: str, include_deleted: bool = False) -> str:
    resolved_case_id = _case_id(case_id)
    store = CaseTimelineEventSqliteStore(db_path)
    records = store.list_events_sorted(client_id=client_id, case_id=resolved_case_id, include_deleted=include_deleted)
    audit_rows = [
        row
        for row in store.audit_rows()
        if str(row.get("client_id") or "") == client_id and str(row.get("case_id") or "") == resolved_case_id
    ]
    latest_actions = sorted(audit_rows, key=lambda row: str(row.get("timestamp") or ""))[-5:]

    lines = [
        "# Caso Finca Timeline SQLite Export",
        "",
        f"DB path: {Path(db_path)}",
        f"client_id: {client_id}",
        f"case_id: {resolved_case_id}",
        f"generated_at: {_generated_at()}",
        "",
        "WARNING: temp/fixture SQLite diagnostic only. This is not production timeline persistence.",
        "",
        "## Timeline",
        "",
        render_sqlite_timeline_events_for_user(records, include_deleted=include_deleted),
        "",
        "## Audit Summary",
        "",
        f"Audit rows: {len(audit_rows)}",
    ]

    if latest_actions:
        lines.extend(["", "Latest actions:"])
        for row in latest_actions:
            action = str(row.get("action") or "")
            actor = str(row.get("actor") or "")
            timestamp = str(row.get("timestamp") or "")
            reason = str(row.get("reason") or "").strip()
            detail = f"- {timestamp} · {action} · actor={actor}"
            if reason:
                detail += f" · reason={reason}"
            lines.append(detail)
    else:
        lines.append("Latest actions: none")

    lines.extend(
        [
            "",
            "## Safety Notes",
            "",
            "- This report is not legal advice.",
            "- Source labels and confirmation status matter.",
            "- Nora/la abogada confirms legal effect.",
            "- Event IDs and internal storage IDs are omitted from this normal operator report.",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export a safe operator report from a temp Caso Finca timeline SQLite DB.")
    parser.add_argument("--db-path", required=True, help="Required temp SQLite DB path. Non-/tmp paths are refused.")
    parser.add_argument("--client-id", default="karen", help="Client ID to filter. Default: karen")
    parser.add_argument("--case-id", default="caso_finca", help="Case/workspace ID or alias. Default: caso_finca")
    parser.add_argument("--include-deleted", action="store_true", help="Include soft-deleted events in a diagnostic section.")
    args = parser.parse_args(argv)

    try:
        report = build_report(
            args.db_path,
            client_id=str(args.client_id or "").strip(),
            case_id=str(args.case_id or "").strip(),
            include_deleted=bool(args.include_deleted),
        )
    except Exception as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2

    print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
