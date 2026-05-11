import re

from memory_store import get_active_case_id, _get_conn
from vfms.vfms import query_db


SEARCH_MARKERS = (
    "busca ",
    "buscar ",
    "qué documento",
    "que documento",
    "qué pdf",
    "que pdf",
    "dónde sale",
    "donde sale",
    "menciona",
)


def _extract_query(text: str) -> str:
    t = (text or "").strip()

    patterns = [
        r"busca\s+(.+)",
        r"buscar\s+(.+)",
        r"qué documento menciona\s+(.+)",
        r"que documento menciona\s+(.+)",
        r"dónde sale\s+(.+)",
        r"donde sale\s+(.+)",
    ]

    for p in patterns:
        m = re.search(p, t, re.I)
        if m:
            q = m.group(1).strip()

            # normalize shorthand legal references
            m2 = re.search(
                r"escritura\s+(\d+)",
                q,
                flags=re.I
            )

            if m2:
                q = m2.group(1)

            return q.strip()

    return t.strip()


async def maybe_handle_document_semantic_query(update, context, chat_id: int, text: str) -> bool:
    raw = (text or "").strip().lower()

    if not any(m in raw for m in SEARCH_MARKERS):
        return False

    case_id = get_active_case_id(int(chat_id))
    if not case_id:
        return False

    query = _extract_query(text)

    if not query:
        return False

    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT note_text
        FROM case_notes
        WHERE case_id=?
          AND source='telegram_attachment_vfms'
        ORDER BY id DESC
        LIMIT 100
        """,
        (case_id,)
    )

    note_rows = cur.fetchall()
    conn.close()

    allowed_ingest_ids = set()

    for row in note_rows:
        note = row[0] if not isinstance(row, dict) else row["note_text"]

        m = re.search(r"- VFMS ingest_id:\s*(.+)", note or "")

        if m:
            allowed_ingest_ids.add(m.group(1).strip())

    rows = []

    for ingest_id in allowed_ingest_ids:
        try:
            matches = query_db(
                query,
                top=5,
                ingest_id=ingest_id
            )

            rows.extend(matches)

        except Exception:
            pass

    rows = rows[:5]

    if not rows:
        await update.message.reply_text(
            f"No encontré coincidencias para: {query}"
        )
        return True

    lines = [f"🔎 Coincidencias para: {query}\n"]

    seen = set()

    for ingest_id, filename, chunk_id, chunk_text in rows:
        key = f"{filename}:{chunk_id}"

        if key in seen:
            continue

        seen.add(key)

        clean = chunk_text.replace("\n", " ").strip()

        idx = clean.lower().find(query.lower())

        if idx >= 0:
            start = max(0, idx - 120)
            end = min(len(clean), idx + 220)
            snippet = clean[start:end].strip()
        else:
            snippet = clean[:260].strip()

        if start > 0:
            snippet = "…" + snippet

        if end < len(clean):
            snippet = snippet + "…"

        lines.append(f"📄 {filename}")
        lines.append(f"VFMS: {ingest_id}")
        lines.append("Coincidencia:")
        lines.append(f"“{snippet}”")
        lines.append("")

    await update.message.reply_text("\n".join(lines).strip())
    return True
