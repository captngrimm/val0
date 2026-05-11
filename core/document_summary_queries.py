import re
from pathlib import Path

from memory_store import get_active_case_id, _get_conn


SUMMARY_MARKERS = (
    "resumen de documentos",
    "resumen documentos",
    "resumen de los documentos",
    "dame resumen de documentos",
    "dame un resumen de documentos",
    "resumen del documento",
    "resume documentos",
    "resume los documentos",
    "qué dicen los documentos",
    "que dicen los documentos",
    "qué dicen los pdf",
    "que dicen los pdf",
)

EXTRACTED_DIR = Path("/opt/val0/vfms_data/extracted")


def _clean_filename(filename: str) -> str:
    filename = (filename or "documento").strip()
    if "__" in filename:
        filename = filename.split("__", 1)[1].strip()
    return filename or "documento"


def _parse_note(note: str) -> dict:
    note = note or ""

    file_match = re.search(r"- Archivo:\s*(.+)", note)
    vfms_match = re.search(r"- VFMS ingest_id:\s*(.+)", note)
    caption_match = re.search(r"- Nota usuario:\s*(.+)", note)
    state_match = re.search(r"- Estado:\s*(.+)", note)

    return {
        "filename": _clean_filename(file_match.group(1).strip()) if file_match else "documento",
        "ingest_id": vfms_match.group(1).strip() if vfms_match else "",
        "caption": caption_match.group(1).strip() if caption_match else "",
        "state": state_match.group(1).strip() if state_match else "",
    }


def _read_extracted_text(ingest_id: str) -> str:
    ingest_id = (ingest_id or "").strip()
    if not ingest_id:
        return ""

    path = EXTRACTED_DIR / f"{ingest_id}.txt"
    if not path.exists():
        return ""

    return path.read_text(encoding="utf-8", errors="replace").strip()


def _normalize_body(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"---\s*page\s+\d+(?:\s*\(ocr\))?\s*---", " ", text, flags=re.I)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _clean_lines(text: str) -> list[str]:
    out = []
    for line in (text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        if re.match(r"---\s*page\s+\d+(?:\s*\(ocr\))?\s*---", line, flags=re.I):
            continue
        out.append(line)
    return out


def _pick_grounded_bullets(text: str, limit: int = 6) -> list[str]:
    lines = _clean_lines(text)
    picked = []

    priority_markers = (
        "caso",
        "base del caso",
        "documentos mencionados",
        "datos registrales",
        "finca",
        "folio",
        "tomo",
        "rollo",
        "escritura",
        "siguiente acción",
        "siguiente accion",
        "abogado",
        "juzgado",
        "registro público",
        "registro publico",
    )

    for line in lines:
        low = line.lower()
        if any(m in low for m in priority_markers):
            picked.append(line)
        if len(picked) >= limit:
            break

    if not picked:
        for line in lines[:limit]:
            picked.append(line)

    # Keep bullets readable.
    clean = []
    seen = set()
    for item in picked:
        item = re.sub(r"\s+", " ", item).strip()
        if not item:
            continue
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        if len(item) > 220:
            item = item[:217].rstrip() + "..."
        clean.append(item)

    return clean[:limit]


def _doc_summary(filename: str, ingest_id: str, caption: str, state: str, text: str) -> str:
    bullets = _pick_grounded_bullets(text)

    lines = [
        f"📄 {_clean_filename(filename)}",
        f"VFMS: {ingest_id}",
    ]

    if caption:
        lines.append(f"Nota: {caption}")

    if state:
        lines.append(f"Estado: {state}")

    if bullets:
        lines.append("Resumen grounded:")
        for b in bullets:
            lines.append(f"- {b}")
    else:
        lines.append("Resumen grounded:")
        lines.append("- No hay texto extraído suficiente para resumir este documento.")

    return "\n".join(lines)


async def maybe_handle_document_summary_query(update, context, chat_id: int, text: str) -> bool:
    raw = (text or "").strip().lower()

    if not any(m in raw for m in SUMMARY_MARKERS):
        return False

    case_id = get_active_case_id(int(chat_id))
    if not case_id:
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

    rows = cur.fetchall()
    conn.close()

    docs = []
    seen_ingest = set()
    seen_body = set()

    for row in rows:
        note = row[0] if not isinstance(row, dict) else row["note_text"]
        parsed = _parse_note(note)

        ingest_id = parsed["ingest_id"]
        if not ingest_id or ingest_id in seen_ingest:
            continue

        text_body = _read_extracted_text(ingest_id)
        body_key = _normalize_body(text_body)

        # Avoid repeating identical extracted documents.
        if body_key and body_key in seen_body:
            continue

        seen_ingest.add(ingest_id)
        if body_key:
            seen_body.add(body_key)

        docs.append({
            **parsed,
            "text": text_body,
        })

        if len(docs) >= 5:
            break

    if not docs:
        await update.message.reply_text(
            f"No encontré documentos extraídos para resumir en CASE:{case_id}."
        )
        return True

    parts = [
        f"🧾 Resumen grounded de documentos para CASE:{case_id}",
        "Sin inferencias. Solo basado en texto extraído/VFMS.\n",
    ]

    for doc in docs:
        parts.append(
            _doc_summary(
                doc["filename"],
                doc["ingest_id"],
                doc["caption"],
                doc["state"],
                doc["text"],
            )
        )
        parts.append("")

    await update.message.reply_text("\n".join(parts).strip())
    return True
