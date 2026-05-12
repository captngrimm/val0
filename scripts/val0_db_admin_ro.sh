#!/usr/bin/env bash
set -euo pipefail

export VAL0_DB_PATH="${VAL0_DB_PATH:-/opt/val0/val0_memory.enc.db}"
export VAL0_DB_KEY_FILE="${VAL0_DB_KEY_FILE:-/etc/val0/db_key}"

cd /opt/val0

case "${1:-help}" in
  help)
    echo "Val0 DB Admin Readonly Helper"
    echo
    echo "Commands:"
    echo "  find_bad_karen_note"
    echo "  recent_karen_notes"
    ;;

  find_bad_karen_note)
    /opt/val0/.venv/bin/python - <<'PY'
from memory_store import fetch_case_notes

chat_id = 8660371933
case_id = "KAREN-LAND-001"
needle = "prepara un paquete para la abogada Nora Santa"

notes = fetch_case_notes(chat_id, case_id, limit=250)
found = 0

for n in notes:
    d = dict(n) if hasattr(n, "keys") else {}
    text = d.get("note_text") or ""
    if needle in text:
        found += 1
        print("FOUND_BAD_NOTE=YES")
        print("id=", d.get("id"))
        print("source=", d.get("source"))
        print("created_at=", d.get("created_at"))
        print("text=", text[:1200])
        print("---")

print(f"FOUND_COUNT={found}")
PY
    ;;

  recent_karen_notes)
    /opt/val0/.venv/bin/python - <<'PY'
from memory_store import fetch_case_notes

chat_id = 8660371933
case_id = "KAREN-LAND-001"

notes = fetch_case_notes(chat_id, case_id, limit=20)

for n in notes:
    d = dict(n) if hasattr(n, "keys") else {}
    print("id=", d.get("id"), "| source=", d.get("source"), "| created_at=", d.get("created_at"))
    print((d.get("note_text") or "")[:500])
    print("---")
PY
    ;;

  *)
    echo "Unknown command: $1" >&2
    exit 2
    ;;
esac
