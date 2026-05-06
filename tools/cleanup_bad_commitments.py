#!/usr/bin/env python3
"""
Safe cleanup for polluted Val0 commitments.

Dry run:
  /opt/val0/.venv/bin/python tools/cleanup_bad_commitments.py --chat-id 1789350565

Confirm:
  /opt/val0/.venv/bin/python tools/cleanup_bad_commitments.py --chat-id 1789350565 --confirm

Rules:
- Does not delete rows.
- Only marks matching open rows as done.
- Dry-run by default.
"""

import argparse
import re
import sys
from pathlib import Path
from datetime import datetime, date

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from memory_store import _get_conn


BAD_EXACT = {
    "qué debo hacer hoy",
    "que debo hacer hoy",
    "val qué debo hacer hoy",
    "val que debo hacer hoy",
    "¿qué debo hacer hoy?",
    "¿que debo hacer hoy?",
}

BAD_PREFIXES = (
    "recuérdame ",
    "recuerdame ",
    "recordatorio ",
)

STALE_TEST_PATTERNS = (
    "tengo que revisar sentinel ahora mismo",
    "tengo que llamar a noah ahora mismo",
    "tengo que llamar al cliente test mañana",
    "registrar en caso: tengo que llamar al cliente test mañana",
)

def norm(s: str) -> str:
    s = (s or "").strip().lower()
    s = s.replace("¿", "").replace("?", "")
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def is_old_due(due: str, cutoff: str) -> bool:
    due = (due or "").strip()
    if not due:
        return False
    return due[:10] < cutoff

def should_close(raw_input: str, due_date: str, cutoff: str) -> tuple[bool, str]:
    n = norm(raw_input)

    if n in BAD_EXACT:
        return True, "question_saved_as_task"

    if any(n.startswith(p) for p in BAD_PREFIXES):
        return True, "reminder_saved_as_task"

    if any(p in n for p in STALE_TEST_PATTERNS):
        return True, "stale_test_task"

    if is_old_due(due_date, cutoff):
        return True, "old_open_task"

    return False, ""

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chat-id", required=True, type=int)
    parser.add_argument("--cutoff", default=date.today().isoformat(), help="Close open tasks due before this YYYY-MM-DD date")
    parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args()

    conn = _get_conn()
    cur = conn.cursor()

    rows = cur.execute(
        """
        SELECT id, raw_input, action, target, due_date, status
        FROM commitments
        WHERE chat_id=? AND status=?
        ORDER BY id ASC
        """,
        (int(args.chat_id), "open"),
    ).fetchall()

    matches = []
    keep = []

    for r in rows:
        row = dict(r)
        ok, reason = should_close(row.get("raw_input"), row.get("due_date"), args.cutoff)
        if ok:
            row["cleanup_reason"] = reason
            matches.append(row)
        else:
            keep.append(row)

    print("===== BAD COMMITMENT CLEANUP =====")
    print(f"chat_id: {args.chat_id}")
    print(f"cutoff: {args.cutoff}")
    print(f"mode: {'CONFIRM' if args.confirm else 'DRY RUN'}")
    print("")
    print(f"open rows scanned: {len(rows)}")
    print(f"rows to mark done: {len(matches)}")
    print(f"rows to keep open: {len(keep)}")
    print("")

    print("===== TO MARK DONE =====")
    for r in matches:
        print(f"#{r['id']} [{r['cleanup_reason']}] {r['due_date']} :: {r['raw_input']}")

    print("")
    print("===== KEEP OPEN =====")
    for r in keep:
        print(f"#{r['id']} {r['due_date']} :: {r['raw_input']}")

    if not args.confirm:
        print("")
        print("Dry run only. Nothing changed.")
        print("To apply: rerun with --confirm")
        conn.close()
        return 0

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    ids = [int(r["id"]) for r in matches]

    if ids:
        placeholders = ",".join("?" for _ in ids)
        cur.execute(
            f"""
            UPDATE commitments
            SET status='done', completed_at=COALESCE(completed_at, ?)
            WHERE chat_id=? AND id IN ({placeholders})
            """,
            [now, int(args.chat_id), *ids],
        )
        print("")
        print(f"Updated rows: {cur.rowcount}")

    conn.commit()
    conn.close()
    print("Cleanup complete.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
