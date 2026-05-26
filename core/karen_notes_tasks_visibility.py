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


def _note_is_user_visible(row: Any) -> bool:
    source = str(_row_value(row, "source", 5, "") or "").strip()
    text = str(_row_value(row, "note_text", 4, "") or "").strip()
    if not text:
        return False
    if source == "telegram_attachment_vfms":
        return False
    return True


def render_karen_case_notes_view(notes: Iterable[Any], *, case_id: str = CASE_KEY, limit: int = 8) -> str:
    visible = [row for row in (notes or ()) if _note_is_user_visible(row)]
    lines = ["📝 Notas de finca/caso", ""]
    if not visible:
        lines.extend([
            "No encontré notas guardadas para la finca/caso todavía.",
            "",
            "Para guardar una, dime: “Val, guarda nota de finca: ...”",
            "Modo: lectura solamente. No creé, cambié ni borré nada.",
        ])
        return "\n".join(lines)

    for idx, row in enumerate(visible[: max(1, int(limit or 8))], start=1):
        note_text = _clean_line(_row_value(row, "note_text", 4, ""))
        created_at = str(_row_value(row, "created_at", 7, "") or "").strip()
        date_label = created_at[:10] if created_at else "sin fecha"
        lines.append(f"{idx}. {date_label} · {note_text}")

    lines.extend([
        "",
        f"Mostré hasta {max(1, int(limit or 8))} notas recientes.",
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
        raw = _clean_line(_row_value(row, "raw_input", 1, ""))
        if not raw:
            action = _clean_line(_row_value(row, "action", 2, ""))
            target = _clean_line(_row_value(row, "target", 3, ""))
            raw = " ".join(part for part in (action, target) if part).strip() or "tarea sin título"
        due = str(_row_value(row, "due_date", 4, "") or "").strip()
        due_label = due[:16].replace("T", " ") if due else "sin fecha"
        lines.append(f"{idx}. {raw} — {due_label}")

    lines.extend([
        "",
        "Puedes decir: “pon esta tarea para mañana” o “márcala como hecha”.",
        "Modo: lectura solamente. No creé, cambié ni borré nada.",
    ])
    return "\n".join(lines)
