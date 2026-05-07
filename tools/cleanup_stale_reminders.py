#!/usr/bin/env python3
"""
Safe cleanup for stale Val0 reminders.

Dry run:
  /opt/val0/.venv/bin/python tools/cleanup_stale_reminders.py --chat-id 1789350565

Confirm:
  /opt/val0/.venv/bin/python tools/cleanup_stale_reminders.py --chat-id 1789350565 --confirm

Rules:
- Does not delete rows.
- Only marks past-due pending/sending reminders as cancelled.
- Dry-run by default.
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from memory_store import _get_conn


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chat-id", required=True, type=int)
    parser.add_argument(
        "--cutoff-utc",
        default=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        help="Cancel pending/sending reminders due before this UTC timestamp",
    )
    parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args()

    conn = _get_conn()
    cur = conn.cursor()

    rows = cur.execute(
        """
        SELECT id, text, due_at_utc, status, created_at
        FROM reminders
        WHERE chat_id=?
          AND status IN (?, ?)
          AND due_at_utc < ?
        ORDER BY due_at_utc ASC, id ASC
        """,
        (int(args.chat_id), "pending", "sending", args.cutoff_utc),
    ).fetchall()

    print("===== STALE REMINDER CLEANUP =====")
    print(f"chat_id: {args.chat_id}")
    print(f"cutoff_utc: {args.cutoff_utc}")
    print(f"mode: {'CONFIRM' if args.confirm else 'DRY RUN'}")
    print("")
    print(f"rows to mark cancelled: {len(rows)}")
    print("")

    for r in rows:
        row = dict(r)
        print(f"#{row['id']} [{row['status']}] {row['due_at_utc']} :: {row['text']}")

    if not args.confirm:
        print("")
        print("Dry run only. Nothing changed.")
        print("To apply: rerun with --confirm")
        conn.close()
        return 0

    ids = [int(dict(r)["id"]) for r in rows]

    if ids:
        placeholders = ",".join("?" for _ in ids)
        cur.execute(
            f"""
            UPDATE reminders
            SET status='cancelled',
                sent_at=COALESCE(sent_at, datetime('now'))
            WHERE chat_id=?
              AND id IN ({placeholders})
            """,
            [int(args.chat_id), *ids],
        )
        print("")
        print(f"Updated rows: {cur.rowcount}")

    conn.commit()
    conn.close()

    print("Cleanup complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
