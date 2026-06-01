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
    norm = re.sub(r"^(bal|pal|val|valeria|vale|va\s+el)\s+", "", norm).strip()
    norm = re.sub(r"^(a ver|bueno|ok|okay|oye)\s+", "", norm).strip()
    return norm


def _number_word_to_int(value: str) -> int | None:
    norm = normalize_visibility_prompt(value)
    if norm.isdigit():
        return int(norm)
    return {
        "uno": 1,
        "una": 1,
        "primer": 1,
        "primero": 1,
        "dos": 2,
        "segundo": 2,
        "tres": 3,
        "tercero": 3,
        "cuatro": 4,
        "cinco": 5,
        "seis": 6,
        "siete": 7,
        "ocho": 8,
        "nueve": 9,
        "diez": 10,
    }.get(norm)


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
    if re.fullmatch(r"que\s+tareas?\s+tengo\s+activas?", norm):
        return True
    if re.fullmatch(r"que\s+tareas?\s+activas?\s+tengo", norm):
        return True
    if re.fullmatch(r"que\s+tareas?\s+tengo", norm):
        return True
    return norm in {
        "que tareas tengo",
        "que tarea tengo",
        "que tarea activa tengo",
        "que tarea tengo activa",
        "que tareas tengo activa",
        "que tareas activas tengo",
        "que tareas pendientes tengo",
        "cuales son mis tareas registradas",
        "cuáles son mis tareas registradas",
        "que tareas registradas tengo",
        "que tareas activas hay",
        "que tareas tengo pendientes",
        "tareas pendientes",
        "mis tareas",
        "mis tareas pendientes",
        "pendientes",
    }


def parse_karen_task_schedule_for_tomorrow(text: str) -> dict[str, Any] | None:
    norm = normalize_visibility_prompt(text)
    if "para manana" not in norm:
        return None
    if not re.search(r"\b(pon|registra|agenda|programa|cambia)\b", norm):
        return None

    number_match = re.search(
        r"\b(?:pon|registra|agenda|programa|cambia)\s+la\s+tarea\s+(?P<num>\d{1,2}|uno|una|primer|primero|dos|segundo|tres|tercero|cuatro|cinco|seis|siete|ocho|nueve|diez)\s+para\s+manana\b",
        norm,
    )
    if number_match:
        return {"number": _number_word_to_int(number_match.group("num")), "target": "", "current": False}

    if re.search(r"\b(?:pon|registra|agenda|programa)\s+esta\s+tarea\s+para\s+manana\b", norm):
        return {"number": None, "target": "", "current": True}

    target_patterns = (
        r"\b(?:pon|registra|agenda|programa)\s+la\s+tarea\s+de\s+(?P<target>.+?)\s+para\s+manana\b",
        r"\b(?:pon|registra|agenda|programa)\s+(?P<target>.+?)\s+para\s+manana\b",
    )
    for pattern in target_patterns:
        match = re.search(pattern, norm)
        if not match:
            continue
        target = _clean_line(match.group("target"), limit=120)
        if target and target not in {"la tarea", "esta tarea"}:
            return {"number": None, "target": target, "current": False}
    return None


def looks_like_karen_task_schedule_for_tomorrow(text: str) -> bool:
    return parse_karen_task_schedule_for_tomorrow(text) is not None


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


def _task_text(row: Any) -> str:
    raw = _clean_line(_row_value(row, "raw_input", 1, ""), limit=120)
    if raw:
        return raw
    action = _clean_line(_row_value(row, "action", 2, ""), limit=60)
    target = _clean_line(_row_value(row, "target", 3, ""), limit=80)
    return " ".join(part for part in (action, target) if part).strip()


def _task_due(row: Any) -> str:
    return str(_row_value(row, "due_date", 4, "") or "").strip()


def _task_source(row: Any) -> str:
    return str(_row_value(row, "source_type", 8, "") or _row_value(row, "source", 8, "") or "").strip()


def is_auxiliary_task_row(row: Any) -> bool:
    return _task_source(row) == "auxiliary_task"


def looks_like_reminder_command_task(text: Any) -> bool:
    norm = normalize_visibility_prompt(str(text or ""))
    if norm.startswith(("recuerdame", "recordatorio")):
        return True
    if norm.startswith(("val recuerdame", "vale recuerdame", "bal recuerdame")):
        return True
    return "recuerdame" in norm and bool(re.search(r"\b(manana|mañana|hoy|a las|am|pm|mediodia|medio dia|md|\d{1,2}:\d{2})\b", norm))


def _looks_like_auxiliary_task_item(text: str) -> bool:
    norm = _note_key(text)
    if not norm:
        return False
    return norm.startswith((
        "pedir ",
        "llamar ",
        "escribir ",
        "revisar ",
        "llevar ",
        "conseguir ",
        "solicitar ",
        "mandar ",
        "enviar ",
    ))


def auxiliary_task_items_from_lines(lines: Iterable[str]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for line in lines or ():
        item = str(line or "").strip()
        if item.startswith("- "):
            item = item[2:].strip()
        item = item.strip(" -\t")
        if not item or item.startswith("#") or item.startswith("_"):
            continue
        if not _looks_like_auxiliary_task_item(item):
            continue
        out.append({
            "id": f"aux:{_note_key(item)}",
            "raw_input": _clean_line(item, limit=120),
            "action": "",
            "target": "",
            "due_date": "",
            "status": "open",
            "source_type": "auxiliary_task",
        })
    return out


def load_karen_auxiliary_task_items(client_id: str | None) -> list[dict[str, Any]]:
    try:
        from core.client_context_reader import load_client_context
    except Exception:
        return []

    try:
        context = load_client_context(client_id or "")
    except Exception:
        return []

    grocery = str(context.get("grocery") or "")
    lines = [line for line in grocery.splitlines() if line.strip().startswith("- ")]
    return auxiliary_task_items_from_lines(lines)


def merge_karen_task_items(tasks: Iterable[Any], auxiliary_tasks: Iterable[Any] | None = None) -> list[Any]:
    merged: list[Any] = []
    seen: set[str] = set()
    for row in list(tasks or ()) + list(auxiliary_tasks or ()):
        text = _task_text(row)
        key = _note_key(text)
        if not key or key in seen:
            continue
        seen.add(key)
        merged.append(row)
    return merged


def select_karen_task_for_schedule(rows: Iterable[Any], request: dict[str, Any]) -> tuple[Any | None, str]:
    task_rows = list(rows or ())
    number = request.get("number")
    target = _note_key(str(request.get("target") or ""))
    current = bool(request.get("current"))

    if number is not None:
        try:
            idx = int(number)
        except Exception:
            return None, "invalid_number"
        if idx < 1 or idx > len(task_rows):
            return None, "not_found"
        return task_rows[idx - 1], "ok"

    if current:
        if len(task_rows) == 1:
            return task_rows[0], "ok"
        return None, "ambiguous"

    if target:
        matches = []
        target_terms = [term for term in target.split() if len(term) > 2]
        for row in task_rows:
            row_key = _note_key(_task_text(row))
            if target in row_key or (target_terms and all(term in row_key for term in target_terms)):
                matches.append(row)
        if len(matches) == 1:
            return matches[0], "ok"
        if len(matches) > 1:
            return None, "ambiguous"
    return None, "not_found"


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
    auxiliary_tasks: Iterable[Any] | None = None,
    limit: int = 5,
) -> str:
    task_rows = merge_karen_task_items(tasks, auxiliary_tasks)[: max(1, int(limit or 5))]
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
            raw = _clean_line(_task_text(row), limit=96) or "tarea sin título"
            due = _task_due(row)
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
    dated_tasks = [row for row in task_rows if _task_due(row)]
    if clean_actionable:
        next_action = clean_actionable[0]["text"]
    elif dated_tasks:
        next_action = _clean_line(_task_text(dated_tasks[0]), limit=96) or "revisar la primera tarea con fecha"
    elif actionable_notes:
        next_action = actionable_notes[0]["text"]
    elif task_rows:
        next_action = _clean_line(_task_text(task_rows[0]), limit=96) or "revisar la primera tarea pendiente"
    elif documents:
        next_action = "revisar el primer documento marcado arriba"
    else:
        next_action = "guardar una tarea o nota concreta si aparece un pendiente nuevo"
    next_action = _clean_line(next_action, limit=110)

    lines.extend([
        "",
        f"Siguiente paso sugerido: {next_action}.",
    ])
    return "\n".join(lines)


def render_karen_tasks_view(tasks: Iterable[Any], *, auxiliary_tasks: Iterable[Any] | None = None, limit: int = 10) -> str:
    rows = merge_karen_task_items(tasks, auxiliary_tasks)
    lines = ["📌 Tareas pendientes", ""]
    if not rows:
        lines.extend([
            "No encontré tareas abiertas para este chat.",
            "",
            "Puedes crear una con: “Val, tengo que ...”.",
        ])
        return "\n".join(lines)

    for idx, row in enumerate(rows[: max(1, int(limit or 10))], start=1):
        raw = _clean_line(_task_text(row), limit=96) or "tarea sin título"
        due = _task_due(row)
        due_label = due[:16].replace("T", " ") if due else "sin fecha"
        marker = " · Posible recordatorio guardado como tarea" if looks_like_reminder_command_task(raw) else ""
        lines.append(f"{idx}. {raw} — {due_label}{marker}")

    lines.extend([
        "",
        "Puedes decir: “marca como hecha la tarea 1”, “elimina la tarea 1” o “pon esta tarea para mañana”.",
    ])
    if any(is_auxiliary_task_row(row) for row in rows):
        lines.append("Algunas tareas sin fecha pueden necesitar que las convierta a tarea formal antes de cerrarlas.")
    return "\n".join(lines)
