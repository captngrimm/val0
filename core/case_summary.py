from memory_store import (
    fetch_case_notes,
    upsert_case_summary,
    _get_conn,
)


def build_case_summary(chat_id: int, case_id: str) -> dict:
    case_id = (case_id or "").strip()
    if not case_id:
        return {}

    # Notes (expediente-based)
    notes = fetch_case_notes(chat_id, case_id, limit=5)

    last_note_at = None
    last_note_text = None

    if notes:
        last_note_at = notes[0].get("created_at")
        last_note_text = notes[0].get("note_text")

    # Events (mixed reality)
    next_deadline = None
    open_reminders_count = 0
    last_event_at = None

    try:
        conn = _get_conn()
        cur = conn.cursor()

        rows = []

        # Existing system reality:
        # case_events often uses numeric-style case_id, while notes/cockpit
        # are expediente-based. Reuse current semantics; do not normalize here.
        try:
            cid_int = int(case_id)
        except Exception:
            cid_int = None

        if cid_int is not None:
            cur.execute(
                """
                SELECT event_text, deadline_date, created_at
                FROM case_events
                WHERE chat_id=?
                  AND case_id=?
                  AND deadline_date IS NOT NULL
                ORDER BY deadline_date ASC
                LIMIT 50
                """,
                (int(chat_id), cid_int),
            )
            rows = cur.fetchall() or []

        conn.close()

        legal_terms = []
        reminders = []

        for r in rows:
            txt = (r["event_text"] if hasattr(r, "keys") else r[0]) or ""
            ddl = (r["deadline_date"] if hasattr(r, "keys") else r[1]) or None
            created_at = (r["created_at"] if hasattr(r, "keys") else r[2]) or None

            if created_at and not last_event_at:
                last_event_at = created_at

            if not ddl:
                continue

            if txt.strip().upper().startswith("RECORDATORIO:"):
                reminders.append((ddl, txt))
            else:
                legal_terms.append((ddl, txt))

        if legal_terms:
            next_deadline = legal_terms[0][0]

        open_reminders_count = len(reminders)

    except Exception:
        pass

    # Build deterministic summary text
    lines = []
    lines.append(f"CASE:{case_id}")

    if last_note_text:
        lines.append(f"Última nota: {last_note_text[:80]}")
    else:
        lines.append("Última nota: —")

    if next_deadline:
        lines.append(f"Próximo término: {next_deadline}")
    else:
        lines.append("Próximo término: —")

    lines.append(f"Recordatorios pendientes: {open_reminders_count}")

    summary_text = "\n".join(lines)

    return {
        "chat_id": int(chat_id),
        "case_id": str(case_id),
        "summary_text": summary_text,
        "last_event_at": last_event_at,
        "last_note_at": last_note_at,
        "next_deadline": next_deadline,
        "open_reminders_count": int(open_reminders_count),
        "summary_version": 1,
    }


def refresh_case_summary(chat_id: int, case_id: str) -> dict:
    data = build_case_summary(chat_id, case_id)

    if not data:
        return {}

    upsert_case_summary(**data)
    return data

