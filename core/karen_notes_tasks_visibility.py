from __future__ import annotations

import re
import unicodedata
from typing import Any, Iterable


CASE_KEY = "KAREN-LAND-001"


def normalize_visibility_prompt(text: str) -> str:
    norm = unicodedata.normalize("NFKD", (text or "").lower())
    norm = "".join(ch for ch in norm if not unicodedata.combining(ch))
    norm = re.sub(r"[¿?¡!.,:;]+", " ", norm)
    norm = re.sub(r"\s+", " ", norm).strip()
    norm = re.sub(r"^(a ver|bueno|ok|okay|oye)\s+", "", norm).strip()
    norm = re.sub(r"^(val|valeria|vale)\s+", "", norm).strip()
    norm = re.sub(r"^(a ver|bueno|ok|okay|oye)\s+", "", norm).strip()
    return norm


def looks_like_karen_notes_query(text: str) -> bool:
    norm = normalize_visibility_prompt(text)
    return norm in {
        "que notas tengo de finca",
        "que notas tengo de la finca",
        "notas de finca",
        "notas de la finca",
        "notas del caso",
        "notas de caso",
        "que notas tengo del caso",
        "que notas tengo de caso",
    }


def looks_like_karen_tasks_query(text: str) -> bool:
    norm = normalize_visibility_prompt(text)
    return norm in {
        "que tareas tengo",
        "que tareas tengo pendientes",
        "tareas pendientes",
        "mis tareas",
        "mis tareas pendientes",
        "pendientes",
    }


def looks_like_karen_case_pendientes_query(text: str) -> bool:
    norm = normalize_visibility_prompt(text)
    return norm in {
        "que pendientes tengo de finca",
        "que pendientes tengo de la finca",
        "pendientes de finca",
        "pendientes de la finca",
        "pendientes del caso",
        "pendientes de caso",
        "que falta revisar de finca",
        "que falta revisar de la finca",
        "que falta revisar del caso",
        "que falta revisar con nora",
        "que me falta revisar con nora",
    }


def _row_value(row: Any, key: str, index: int, default: Any = "") -> Any:
    if isinstance(row, dict):
        return row.get(key, default)
    if hasattr(row, "keys"):
        return row[key] if key in row.keys() else default
    try:
        return row[index]
    except Exception:
        return default


def _clean_line(value: Any, *, limit: int = 160) -> str:
    text = " ".join(str(value or "").replace("\n", " ").split()).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip(" .,;:-") + "…"


def _clean_note_text(value: Any) -> tuple[str, bool]:
    text = _clean_line(value, limit=240)
    legacy = False
    lowered = text.lower()
    historical_prefixes = (
        "inventario inicial:",
        "historial inicial:",
        "historia inicial:",
        "contexto inicial:",
        "resumen inicial:",
    )
    for prefix in historical_prefixes:
        if lowered.startswith(prefix):
            text = text[len(prefix):].strip(" :-")
            legacy = True
            break

    lowered = text.lower()
    legacy_prefixes = (
        "cita / agenda del caso:",
        "cita/agenda del caso:",
        "cambio de cita / agenda del caso:",
        "cambio de cita/agenda del caso:",
    )
    for prefix in legacy_prefixes:
        if lowered.startswith(prefix):
            text = text[len(prefix):].strip(" :-")
            legacy = True
            break

    command_pattern = re.compile(
        r"^(?:val[,\s]+)?(?:guarda|guardar|anota|toma)\s+(?:esta\s+)?nota\s+de\s+(?:finca|caso)\s*:?\s*",
        flags=re.IGNORECASE,
    )
    if command_pattern.search(text):
        text = command_pattern.sub("", text).strip(" :-")
        legacy = True

    return _clean_line(text, limit=180), legacy


def _note_key(text: str) -> str:
    norm = unicodedata.normalize("NFKD", text.lower())
    norm = "".join(ch for ch in norm if not unicodedata.combining(ch))
    norm = re.sub(r"[^a-z0-9]+", " ", norm)
    return re.sub(r"\s+", " ", norm).strip()


def _note_is_user_visible(row: Any) -> bool:
    source = str(_row_value(row, "source", 5, "") or "").strip()
    text = str(_row_value(row, "note_text", 4, "") or "").strip()
    if not text:
        return False
    if source == "telegram_attachment_vfms":
        return False
    return True


def _looks_like_legacy_noise(text: str, source: str) -> bool:
    key = _note_key(text)
    if source in {"case_appointment_v0", "case_appointment_reschedule_v0"}:
        return True
    return any(marker in key for marker in (
        "test",
        "prueba",
        "inventario inicial",
        "historial inicial",
        "historia inicial",
        "contexto inicial",
        "resumen inicial",
        "photo",
        "foto prueba",
    ))


def _clean_visible_notes(notes: Iterable[Any]) -> list[dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    for row in notes or ():
        if not _note_is_user_visible(row):
            continue
        raw_text = _row_value(row, "note_text", 4, "")
        text, legacy = _clean_note_text(raw_text)
        key = _note_key(text)
        if not text or not key:
            continue
        created_at = str(_row_value(row, "created_at", 7, "") or "").strip()
        source = str(_row_value(row, "source", 5, "") or "").strip()
        item = {
            "text": text,
            "created_at": created_at,
            "date_label": created_at[:10] if created_at else "sin fecha",
            "legacy": legacy or _looks_like_legacy_noise(text, source),
        }
        previous = by_key.get(key)
        if not previous:
            by_key[key] = item
            continue
        if previous.get("legacy") and not item.get("legacy"):
            by_key[key] = item
        elif previous.get("legacy") == item.get("legacy") and item.get("created_at", "") > previous.get("created_at", ""):
            by_key[key] = item

    items = list(by_key.values())
    items.sort(key=lambda item: (bool(item.get("legacy")), str(item.get("created_at") or "")), reverse=False)
    clean = [item for item in items if not item.get("legacy")]
    legacy = [item for item in items if item.get("legacy")]
    clean.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
    legacy.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
    return clean + legacy


def render_karen_case_notes_view(notes: Iterable[Any], *, case_id: str = CASE_KEY, limit: int = 8) -> str:
    visible = _clean_visible_notes(notes)
    display_limit = max(1, min(int(limit or 5), 5))
    lines = ["📝 Notas de finca/caso", ""]
    if not visible:
        lines.extend([
            "No encontré notas guardadas para la finca/caso todavía.",
            "",
            "Para guardar una, dime: “Val, guarda nota de finca: ...”",
            "Modo: lectura solamente. No creé, cambié ni borré nada.",
        ])
        return "\n".join(lines)

    clean_items = [item for item in visible if not item.get("legacy")]
    legacy_items = [item for item in visible if item.get("legacy")]
    display_items = clean_items[:display_limit]
    if not display_items:
        display_items = legacy_items[:display_limit]

    for idx, item in enumerate(display_items, start=1):
        prefix = "Legado/test · " if item.get("legacy") else ""
        lines.append(f"{idx}. {prefix}{item['date_label']} · {item['text']}")

    hidden_legacy_count = max(0, len(legacy_items) - sum(1 for item in display_items if item.get("legacy")))
    if clean_items and hidden_legacy_count:
        lines.extend(["", f"Oculté {hidden_legacy_count} nota(s) histórica(s)/test para mantener esto limpio."])

    lines.extend([
        "",
        f"Mostré hasta {display_limit} notas recientes.",
        "Modo: lectura solamente. No creé, cambié ni borré nada.",
    ])
    return "\n".join(lines)


def _note_is_actionable(text: str) -> bool:
    norm = _note_key(text)
    return any(marker in norm for marker in (
        "hay que",
        "revisar",
        "falta",
        "pendiente",
        "conseguir",
        "antes de",
        "preparar",
        "llamar",
        "escribir",
    ))


def _document_review_items(notes: Iterable[Any], *, limit: int = 3) -> list[str]:
    items: list[str] = []
    noisy_markers = ("test", "prueba", "old", "viejo", "foto vieja", "photo")
    for row in notes or ():
        source = str(_row_value(row, "source", 5, "") or "").strip()
        if source != "telegram_attachment_vfms":
            continue
        text = str(_row_value(row, "note_text", 4, "") or "")
        filename_match = re.search(r"- Archivo:\s*(.+)", text, flags=re.IGNORECASE)
        status_match = re.search(r"- Estado:\s*(.+)", text, flags=re.IGNORECASE)
        filename = _clean_line(filename_match.group(1) if filename_match else "documento", limit=80)
        status = _clean_line(status_match.group(1) if status_match else "requiere revisión", limit=80)
        key = _note_key(filename)
        if any(marker in key for marker in noisy_markers):
            continue
        items.append(f"{filename} — {status}")
        if len(items) >= max(1, int(limit or 3)):
            break
    return items


def render_karen_case_pendientes_view(
    *,
    tasks: Iterable[Any],
    notes: Iterable[Any],
    limit: int = 5,
) -> str:
    task_rows = list(tasks or [])[: max(1, int(limit or 5))]
    clean_notes = _clean_visible_notes(notes)
    clean_actionable = [
        item for item in clean_notes
        if not item.get("legacy") and _note_is_actionable(str(item.get("text") or ""))
    ]
    legacy_actionable = [
        item for item in clean_notes
        if item.get("legacy") and _note_is_actionable(str(item.get("text") or ""))
    ]
    actionable_notes = (clean_actionable + legacy_actionable)[: max(1, int(limit or 5))]
    documents = _document_review_items(notes, limit=3)

    lines = ["📌 Pendientes de finca/caso", ""]

    lines.append("Tareas")
    if task_rows:
        for idx, row in enumerate(task_rows, start=1):
            raw = _clean_line(_row_value(row, "raw_input", 1, ""), limit=96)
            if not raw:
                raw = _clean_line(" ".join(
                    part for part in (
                        _row_value(row, "action", 2, ""),
                        _row_value(row, "target", 3, ""),
                    )
                    if str(part or "").strip()
                )) or "tarea sin título"
            due = str(_row_value(row, "due_date", 4, "") or "").strip()
            due_label = due[:16].replace("T", " ") if due else "sin fecha"
            lines.append(f"{idx}. {raw} — {due_label}")
    else:
        lines.append("- No encontré tareas abiertas.")

    lines.extend(["", "Notas accionables"])
    if actionable_notes:
        for idx, item in enumerate(actionable_notes, start=1):
            legacy = "Legado/test · " if item.get("legacy") else ""
            lines.append(f"{idx}. {legacy}{item['text']}")
    else:
        lines.append("- No encontré notas accionables claras.")

    lines.extend(["", "Documentos / revisión"])
    if documents:
        for item in documents:
            lines.append(f"- {item}")
    else:
        lines.append("- No encontré documentos recientes de revisión para destacar.")

    next_action = ""
    dated_tasks = [row for row in task_rows if str(_row_value(row, "due_date", 4, "") or "").strip()]
    if clean_actionable:
        next_action = clean_actionable[0]["text"]
    elif dated_tasks:
        next_action = _clean_line(_row_value(dated_tasks[0], "raw_input", 1, ""), limit=96) or "revisar la primera tarea con fecha"
    elif actionable_notes:
        next_action = actionable_notes[0]["text"]
    elif task_rows:
        next_action = _clean_line(_row_value(task_rows[0], "raw_input", 1, ""), limit=96) or "revisar la primera tarea pendiente"
    elif documents:
        next_action = "revisar el primer documento marcado arriba"
    else:
        next_action = "guardar una tarea o nota concreta si aparece un pendiente nuevo"
    next_action = _clean_line(next_action, limit=110)

    lines.extend([
        "",
        f"Siguiente paso sugerido: {next_action}.",
        "Modo: lectura solamente. No creé, cambié ni borré nada.",
    ])
    return "\n".join(lines)


def render_karen_tasks_view(tasks: Iterable[Any], *, limit: int = 10) -> str:
    rows = list(tasks or ())
    lines = ["📌 Tareas pendientes", ""]
    if not rows:
        lines.extend([
            "No encontré tareas abiertas para este chat.",
            "",
            "Puedes crear una con: “Val, tengo que ...”.",
            "Modo: lectura solamente. No creé, cambié ni borré nada.",
        ])
        return "\n".join(lines)

    for idx, row in enumerate(rows[: max(1, int(limit or 10))], start=1):
        raw = _clean_line(_row_value(row, "raw_input", 1, ""), limit=96)
        if not raw:
            action = _clean_line(_row_value(row, "action", 2, ""))
            target = _clean_line(_row_value(row, "target", 3, ""))
            raw = " ".join(part for part in (action, target) if part).strip() or "tarea sin título"
        due = str(_row_value(row, "due_date", 4, "") or "").strip()
        due_label = due[:16].replace("T", " ") if due else "sin fecha"
        lines.append(f"{idx}. {raw} — {due_label}")

    lines.extend([
        "",
        "Puedes decir: “marca como hecha la tarea 1” o “pon esta tarea para mañana”.",
        "Modo: lectura solamente. No creé, cambié ni borré nada.",
    ])
    return "\n".join(lines)
