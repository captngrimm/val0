import re
from memory_store import _get_conn, get_active_case_id

INTENT_PATTERNS = {
    "list_all": [
        "qué documentos",
        "que documentos",
        "qué archivos",
        "que archivos",
    ],
    "pdf_only": [
        "qué pdf",
        "que pdf",
        "pdf",
    ],
    "today_only": [
        "hoy",
    ],
    "caption_only": [
        "caption",
        "nota",
        "descripción",
        "descripcion",
    ],
    "registro_publico": [
        "registro público",
        "registro publico",
    ],
}

def detect_intents(text: str) -> set[str]:
    t = (text or "").lower()
    found = set()

    for intent, markers in INTENT_PATTERNS.items():
        if any(m in t for m in markers):
            found.add(intent)

    return found

def _parse_note(note: str) -> dict:
    note = note or ""

    file_match = re.search(r"- Archivo:\s*(.+)", note)
    vfms_match = re.search(r"- VFMS ingest_id:\s*(.+)", note)
    caption_match = re.search(r"- Nota usuario:\s*(.+)", note)
    state_match = re.search(r"- Estado:\s*(.+)", note)

    return {
        "filename": file_match.group(1).strip() if file_match else "desconocido",
        "vfms_id": vfms_match.group(1).strip() if vfms_match else "?",
        "caption": caption_match.group(1).strip() if caption_match else "",
        "state": state_match.group(1).strip() if state_match else "",
        "raw": note.lower(),
        "has_caption": bool(caption_match and caption_match.group(1).strip()),
    }

async def maybe_handle_document_query(update, context, chat_id: int, text: str) -> bool:
    intents = detect_intents(text)

    if not intents:
        return False

    case_id = get_active_case_id(int(chat_id))
    if not case_id:
        return False

    conn = _get_conn()
    conn.row_factory = None
    cur = conn.cursor()

    cur.execute("""
    select id, created_at, note_text
    from case_notes
    where case_id=?
      and source='telegram_attachment_vfms'
    order by id desc
    limit 100
    """, (case_id,))

    rows = cur.fetchall()
    conn.close()

    # DB already returns newest first

    parsed = []
    seen = set()

    for rid, created_at, note in rows:
        item = _parse_note(note)

        filename = item["filename"]
        caption = item["caption"]
        raw = item["raw"]

        if "pdf_only" in intents:
            if not filename.lower().endswith(".pdf"):
                continue

        if "caption_only" in intents:
            if not item["has_caption"]:
                continue

        if "registro_publico" in intents:
            searchable = f"{filename}\n{caption}\n{raw}".lower()

            registry_markers = (
                "registro público",
                "registro publico",
                "finca",
                "folio",
                "tomo",
                "rollo",
                "escritura",
            )

            if not any(m in searchable for m in registry_markers):
                continue

        dedupe_key = re.sub(
            r"\s+",
            "",
            item["filename"].strip().lower()
        )

        if dedupe_key in seen:
            continue

        seen.add(dedupe_key)

        parsed.append({
            "id": rid,
            "created_at": created_at,
            **item,
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

        if p["vfms_id"]:
            lines.append(f"  VFMS: {p['vfms_id']}")

        if p["state"]:
            lines.append(f"  Estado: {p['state']}")

        lines.append(f"  Registro: #{p['id']} · {p['created_at']}")
        lines.append("")

    await update.message.reply_text("\n".join(lines).strip())
    return True
