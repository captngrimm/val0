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
                flags=re.I,
            )

            if m2:
                q = m2.group(1)

            return q.strip()

    return t.strip()


def _clean_filename(filename: str) -> str:
    filename = (filename or "documento").strip()

    # Telegram/VFMS sometimes stores names as "8456__Document4.pdf".
    if "__" in filename:
        filename = filename.split("__", 1)[1].strip()

    return filename or "documento"


def _normalize_for_dedupe(text: str) -> str:
    text = (text or "").lower()
    text = text.replace("--- page 1 ---", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _make_snippet(chunk_text: str, query: str) -> str:
    clean = (chunk_text or "").replace("\n", " ").strip()
    clean = clean.replace("--- Page 1 ---", "").strip()

    if not clean:
        return ""

    idx = clean.lower().find((query or "").lower())

    if idx >= 0:
        start = max(0, idx - 120)
        end = min(len(clean), idx + 220)
        snippet = clean[start:end].strip()

        if start > 0:
            snippet = "…" + snippet

        if end < len(clean):
            snippet = snippet + "…"

        return snippet

    snippet = clean[:260].strip()

    if len(clean) > 260:
        snippet += "…"

    return snippet


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
        (case_id,),
    )

    note_rows = cur.fetchall()
    conn.close()

    allowed_ingest_ids = []
    seen_ingest_ids = set()

    for row in note_rows:
        note = row[0] if not isinstance(row, dict) else row["note_text"]
        m = re.search(r"- VFMS ingest_id:\s*(.+)", note or "")

        if not m:
            continue

        ingest_id = m.group(1).strip()

        if ingest_id in seen_ingest_ids:
            continue

        seen_ingest_ids.add(ingest_id)
        allowed_ingest_ids.append(ingest_id)

    rows = []

    # Keep newest case-linked attachments first because note_rows are DESC.
    for ingest_id in allowed_ingest_ids:
        try:
            matches = query_db(
                query,
                top=5,
                ingest_id=ingest_id,
            )
            rows.extend(matches)
        except Exception:
            continue

    if not rows:
        await update.message.reply_text(
            f"No encontré coincidencias para: {query}"
        )
        return True

    lines = [f"🔎 Coincidencias para: {query}\n"]

    seen_files = set()
    seen_snippets = set()
    shown = 0

    for ingest_id, filename, chunk_id, chunk_text in rows:
        clean_filename = _clean_filename(filename)
        snippet = _make_snippet(chunk_text, query)

        if not snippet:
            continue

        file_key = clean_filename.lower().strip()
        snippet_key = _normalize_for_dedupe(snippet)

        # Avoid showing the same PDF name repeatedly and collapse repeated body text.
        if file_key in seen_files:
            continue

        if snippet_key in seen_snippets:
            continue

        seen_files.add(file_key)
        seen_snippets.add(snippet_key)

        lines.append(f"📄 {clean_filename}")
        lines.append(f"VFMS: {ingest_id}")
        lines.append("Coincidencia:")
        lines.append(f"“{snippet}”")
        lines.append("")

        shown += 1

        if shown >= 5:
            break

    if shown == 0:
        await update.message.reply_text(
            f"No encontré coincidencias únicas para: {query}"
        )
        return True

    await update.message.reply_text("\n".join(lines).strip())
    return True
