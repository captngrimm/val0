import re
from memory_store import _get_conn, get_active_case_id

DOC_QUERY_MARKERS = (
    "qué documentos",
    "que documentos",
    "qué pdf",
    "que pdf",
    "qué archivos",
    "que archivos",
    "qué subí",
    "que subi",
    "registro público",
    "registro publico",
)

def _matches_doc_query(text: str) -> bool:
    t = (text or "").lower()
    return any(m in t for m in DOC_QUERY_MARKERS)

def _extract_filters(text: str) -> dict:
    t = (text or "").lower()

    return {
        "pdf_only": "pdf" in t,
        "registro_publico": (
            "registro público" in t
            or "registro publico" in t
        ),
        "today_only": "hoy" in t,
    }

async def maybe_handle_document_query(update, context, chat_id: int, text: str) -> bool:
    if not _matches_doc_query(text):
        return False

    case_id = get_active_case_id(int(chat_id))
    if not case_id:
        return False

    filters = _extract_filters(text)

    conn = _get_conn()
    conn.row_factory = None
    cur = conn.cursor()

    cur.execute("""
    select id, created_at, note_text
    from case_notes
    where case_id=?
      and source='telegram_attachment_vfms'
    order by id desc
    limit 50
    """, (case_id,))

    rows = cur.fetchall()
    conn.close()

    parsed = []

    for rid, created_at, note in rows:
        note = note or ""

        file_match = re.search(r"- Archivo:\s*(.+)", note)
        vfms_match = re.search(r"- VFMS ingest_id:\s*(.+)", note)
        caption_match = re.search(r"- Nota usuario:\s*(.+)", note)

        filename = file_match.group(1).strip() if file_match else "desconocido"
        vfms_id = vfms_match.group(1).strip() if vfms_match else "?"
        caption = caption_match.group(1).strip() if caption_match else ""

        if filters["pdf_only"] and not filename.lower().endswith(".pdf"):
            continue

        searchable_blob = f"{filename}\n{caption}\n{note}".lower()

        if filters["registro_publico"]:
            if (
                "registro público" not in searchable_blob
                and "registro publico" not in searchable_blob
            ):
                continue

        parsed.append({
            "id": rid,
            "created_at": created_at,
            "filename": filename,
            "vfms_id": vfms_id,
            "caption": caption,
        })

    if not parsed:
        await update.message.reply_text(
            f"No encontré documentos que coincidan en CASE:{case_id}."
        )
        return True

    lines = [f"📎 Documentos registrados para CASE:{case_id}:\n"]

    for p in parsed[:15]:
        lines.append(f"- {p['filename']}")
        if p["caption"]:
            lines.append(f"  Nota: {p['caption']}")
        lines.append(f"  VFMS: {p['vfms_id']}")
        lines.append(f"  Registro: #{p['id']} · {p['created_at']}")
        lines.append("")

    await update.message.reply_text("\n".join(lines).strip())
    return True
