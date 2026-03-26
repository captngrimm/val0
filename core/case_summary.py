from memory_store import (
    fetch_case_notes,
    upsert_case_summary,
    _get_conn,
)


def build_case_summary(chat_id: int, case_id: str) -> dict:
    case_id = (case_id or "").strip()
    if not case_id:
        return {}

    client_name = None
    latest_note = None
    last_note_at = None
    recent_notes = []
    notes_count = 0

    next_term_text = None
    next_term_date = None
    next_reminder_text = None
    next_reminder_date = None
    open_reminders_count = 0
    open_tasks_count = 0
    last_event_at = None

    # -------------------------
    # Case header
    # -------------------------
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT client_name
            FROM cases
            WHERE chat_id=? AND expediente=?
            ORDER BY id DESC
            LIMIT 1
            """,
            (int(chat_id), str(case_id)),
        )
        row = cur.fetchone()
        conn.close()

        if row:
            client_name = (row["client_name"] if hasattr(row, "keys") else row[0]) or None
    except Exception:
        client_name = None

    # -------------------------
    # Notes (expediente-based)
    # -------------------------
    try:
        notes = fetch_case_notes(chat_id, case_id, limit=20)
    except Exception:
        notes = []

    notes_count = len(notes)

    for n in notes:
        txt = (n.get("note_text") or "").strip()
        if not txt:
            continue

        if latest_note is None:
            latest_note = txt
            last_note_at = n.get("created_at")

        if len(recent_notes) < 3:
            recent_notes.append(txt)

    # -------------------------
    # Events (mixed reality)
    # -------------------------
    try:
        conn = _get_conn()
        cur = conn.cursor()

        rows = []

        try:
            cid_int = int(case_id)
        except Exception:
            cid_int = None

        if cid_int is not None:
            query = """
                SELECT event_text, deadline_date, created_at
                FROM case_events
                WHERE chat_id = ?
                  AND case_id = ?
                  AND (
                        deadline_date IS NOT NULL
                        OR UPPER(event_text) LIKE 'TAREA:%'
                  )
                ORDER BY
                    CASE
                        WHEN deadline_date IS NULL THEN 1
                        ELSE 0
                    END,
                    deadline_date ASC,
                    id DESC
                LIMIT 100
            """
            cur.execute(query, (int(chat_id), cid_int))
            rows = cur.fetchall() or []

        conn.close()

        legal_terms = []
        reminders = []
        tasks = []

        for r in rows:
            txt = (r["event_text"] if hasattr(r, "keys") else r[0]) or ""
            ddl = (r["deadline_date"] if hasattr(r, "keys") else r[1]) or None
            created_at = (r["created_at"] if hasattr(r, "keys") else r[2]) or None

            if created_at and not last_event_at:
                last_event_at = created_at

            txt_upper = txt.strip().upper()

            if txt_upper.startswith("TAREA:"):
                tasks.append((ddl, txt))
                continue

            if not ddl:
                continue

            if txt_upper.startswith("RECORDATORIO:"):
                reminders.append((ddl, txt))
            else:
                legal_terms.append((ddl, txt))

        if legal_terms:
            next_term_date, next_term_text = legal_terms[0]

        if reminders:
            next_reminder_date, next_reminder_text = reminders[0]

        open_reminders_count = len(reminders)
        open_tasks_count = len(tasks)

    except Exception:
        pass

    # -------------------------
    # Build deterministic summary text
    # -------------------------
    summary_lines = []

    summary_lines.append(f"CASE:{case_id}")

    if client_name:
        summary_lines.append(f"Cliente: {client_name}")

    if latest_note:
        summary_lines.append(f"Última nota: {latest_note[:160]}")
    else:
        summary_lines.append("Última nota: —")

    if next_term_text and next_term_date:
        summary_lines.append(f"Próximo término: {next_term_date} | {next_term_text[:160]}")
    elif next_term_date:
        summary_lines.append(f"Próximo término: {next_term_date}")
    else:
        summary_lines.append("Próximo término: —")

    if next_reminder_text and next_reminder_date:
        summary_lines.append(f"Próximo recordatorio: {next_reminder_date} | {next_reminder_text[:160]}")
    elif next_reminder_date:
        summary_lines.append(f"Próximo recordatorio: {next_reminder_date}")
    else:
        summary_lines.append("Próximo recordatorio: —")

    if recent_notes:
        summary_lines.append("Notas recientes:")
        for note_text in recent_notes[:3]:
            summary_lines.append(f"- {note_text[:160]}")
    else:
        summary_lines.append("Notas recientes: —")

    summary_lines.append(f"Notas totales: {notes_count}")
    summary_lines.append(f"Recordatorios pendientes: {open_reminders_count}")
    summary_lines.append(f"Tareas abiertas: {open_tasks_count}")

    summary_text = "\n".join(summary_lines)

    return {
        "chat_id": int(chat_id),
        "case_id": str(case_id),
        "summary_text": summary_text,
        "last_event_at": last_event_at,
        "last_note_at": last_note_at,
        "next_deadline": next_term_date,
        "open_reminders_count": int(open_reminders_count),
        "summary_version": 1,
    }


def refresh_case_summary(chat_id: int, case_id: str) -> dict:
    data = build_case_summary(chat_id, case_id)

    if not data:
        return {}

    upsert_case_summary(**data)
    return data