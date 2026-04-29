#!/usr/bin/env python3
"""
Safe Val0 chat reset tool.

Usage:
  Dry run:
    /opt/val0/.venv/bin/python tools/reset_chat.py --chat-id 8660371933

  Confirmed reset:
    /opt/val0/.venv/bin/python tools/reset_chat.py --chat-id 8660371933 --confirm

Rules:
- Only deletes rows where chat_id matches.
- Never runs without explicit chat_id.
- Dry-run by default.
- Requires --confirm to delete.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from memory_store import _get_conn


RESET_TABLES: List[str] = [
    "action_logs",
    "audit_log",
    "case_events",
    "case_notes",
    "case_summaries",
    "cases",
    "chat_prefs",
    "commitments",
    "daily_logs",
    "legal_audit_log",
    "memory_entries",
    "memory_items",
    "messages",
    "milestones",
    "notes",
    "pm_current_focus",
    "pm_decisions",
    "reminders",
    "tasks",
    "user_facts",
    "user_settings",
]


def table_has_chat_id(cur, table: str) -> bool:
    cols = cur.execute(f"PRAGMA table_info({table})").fetchall()
    for c in cols:
        name = c["name"] if hasattr(c, "keys") else c[1]
        if name == "chat_id":
            return True
    return False


def count_rows(cur, table: str, chat_id: int) -> int:
    row = cur.execute(
        f"SELECT COUNT(*) AS c FROM {table} WHERE chat_id=?",
        (chat_id,),
    ).fetchone()
    return int(row["c"] if hasattr(row, "keys") else row[0])


def main() -> int:
    parser = argparse.ArgumentParser(description="Safely reset all Val0 data for one chat_id.")
    parser.add_argument("--chat-id", required=True, type=int, help="Telegram chat_id to reset")
    parser.add_argument("--confirm", action="store_true", help="Actually delete rows")
    args = parser.parse_args()

    chat_id = int(args.chat_id)

    conn = _get_conn()
    cur = conn.cursor()

    existing_tables = {
        (r["name"] if hasattr(r, "keys") else r[0])
        for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }

    plan: List[Tuple[str, int]] = []

    for table in RESET_TABLES:
        if table not in existing_tables:
            continue
        if not table_has_chat_id(cur, table):
            continue
        n = count_rows(cur, table, chat_id)
        plan.append((table, n))

    total = sum(n for _, n in plan)

    print("===== VAL0 CHAT RESET =====")
    print(f"chat_id: {chat_id}")
    print(f"mode: {'CONFIRM DELETE' if args.confirm else 'DRY RUN'}")
    print("")
    print("Rows by table:")

    for table, n in plan:
        print(f"- {table}: {n}")

    print("")
    print(f"TOTAL: {total}")

    if not args.confirm:
        print("")
        print("Dry run only. Nothing deleted.")
        print("To delete, rerun with --confirm")
        conn.close()
        return 0

    print("")
    print("Deleting rows...")

    for table, n in plan:
        if n <= 0:
            continue
        cur.execute(f"DELETE FROM {table} WHERE chat_id=?", (chat_id,))
        print(f"- {table}: deleted {cur.rowcount}")

    conn.commit()
    conn.close()

    print("")
    print("RESET COMPLETE.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
