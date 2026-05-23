from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
import unicodedata


class ConversationIntent(str, Enum):
    TECHNICAL_PASTE = "technical_paste"
    AGENDA_QUERY = "agenda_query"
    CALENDAR_CREATE_CANDIDATE = "calendar_create_candidate"
    CALENDAR_DELETE_CANDIDATE = "calendar_delete_candidate"
    GROCERY_CANDIDATE = "grocery_candidate"
    LEGAL_FINCA_CANDIDATE = "legal_finca_candidate"
    REMINDER_CANDIDATE = "reminder_candidate"
    HELP_OR_CAPABILITY = "help_or_capability"
    SMALLTALK = "smalltalk"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class NormalizedMessage:
    raw_text: str
    text: str
    normalized_text: str
    without_val_prefix: str
    chat_id: int | None = None
    client_id: str | None = None
    line_count: int = 0
    is_group_chat: bool = False
    is_command: bool = False
    is_technical_paste: bool = False


def _strip_accents(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def _norm(text: str) -> str:
    text = _strip_accents(text).lower()
    text = re.sub(r"[¿?¡!.,:;]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _without_val_prefix(normalized_text: str) -> str:
    text = re.sub(r"^(a ver|bueno|ok|okay|oye)\s+", "", normalized_text).strip()
    text = re.sub(r"^(val|valeria|vale)\s+", "", text).strip()
    text = re.sub(r"^(a ver|bueno|ok|okay|oye)\s+", "", text).strip()
    return text


def looks_like_technical_paste(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False

    low = raw.lower()
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    first = lines[0] if lines else raw
    first_low = first.lower()

    if first.startswith("==="):
        return True

    if first_low.startswith(("```bash", "```sh", "```shell", "```python", "```console")):
        return True

    if re.match(r"^(cd\s+/opt/|sudo\s+|systemctl\s+|journalctl\s+|git\s+(log|status)\b)", first_low):
        return True

    strong_markers = (
        "git log",
        "git status",
        "systemctl",
        "tee /root/launchpad",
        "<<'py'",
        '<<"py"',
        "./scripts/val0py",
    )
    if any(marker in low for marker in strong_markers):
        return True

    if len(lines) >= 4:
        shell_markers = (
            "echo ",
            "python3",
            "./scripts/val0py",
            "git ",
            "systemctl",
            "journalctl",
            "tee ",
            "cat <<",
            "&&",
            "||",
            "{",
            "}",
        )
        hits = sum(1 for marker in shell_markers if marker in low)
        if hits >= 3:
            return True

    return False


def normalize_message(
    text: str,
    chat_id: int | None = None,
    client_id: str | None = None,
) -> NormalizedMessage:
    raw = text or ""
    stripped = raw.strip()
    normalized = _norm(stripped)
    without_prefix = _without_val_prefix(normalized)
    lines = [line for line in raw.splitlines() if line.strip()]
    return NormalizedMessage(
        raw_text=raw,
        text=stripped,
        normalized_text=normalized,
        without_val_prefix=without_prefix,
        chat_id=chat_id,
        client_id=client_id,
        line_count=len(lines),
        is_group_chat=bool(chat_id is not None and int(chat_id) < 0),
        is_command=stripped.startswith("/"),
        is_technical_paste=looks_like_technical_paste(stripped),
    )


def classify_deterministic_intent(message: NormalizedMessage) -> ConversationIntent:
    if message.is_technical_paste:
        return ConversationIntent.TECHNICAL_PASTE

    text = message.without_val_prefix
    if not text:
        return ConversationIntent.UNKNOWN

    if text in {"hola", "buenas", "hello", "hi", "hey"}:
        return ConversationIntent.SMALLTALK

    if any(marker in text for marker in (
        "ayuda",
        "help",
        "comandos",
        "que puedes hacer",
        "que sabes hacer",
        "como me puedes ayudar",
        "capacidades",
    )):
        return ConversationIntent.HELP_OR_CAPABILITY

    if _is_grocery_candidate(text):
        return ConversationIntent.GROCERY_CANDIDATE

    if _is_calendar_delete_candidate(text):
        return ConversationIntent.CALENDAR_DELETE_CANDIDATE

    if _is_calendar_create_candidate(text):
        return ConversationIntent.CALENDAR_CREATE_CANDIDATE

    if _is_reminder_candidate(text):
        return ConversationIntent.REMINDER_CANDIDATE

    if _is_agenda_query(text):
        return ConversationIntent.AGENDA_QUERY

    if _is_legal_finca_candidate(text):
        return ConversationIntent.LEGAL_FINCA_CANDIDATE

    return ConversationIntent.UNKNOWN


def _is_agenda_query(text: str) -> bool:
    markers = (
        "que tengo hoy",
        "que tengo manana",
        "que tengo mañana",
        "que tengo esta semana",
        "que tengo en agenda",
        "mi agenda",
        "proximas citas",
        "proximas citas",
        "que cita tengo",
        "que citas tengo",
    )
    return any(marker in text for marker in markers)


def _is_calendar_create_candidate(text: str) -> bool:
    markers = (
        "tengo cita",
        "tengo una cita",
        "cita con",
        "reunion con",
        "tengo reunion",
        "agenda cita",
        "agendar cita",
        "guarda cita",
        "registrar cita",
    )
    return any(marker in text for marker in markers)


def _is_calendar_delete_candidate(text: str) -> bool:
    delete_markers = ("borra", "borrar", "elimina", "eliminar", "cancela", "cancelar")
    calendar_markers = ("cita", "evento", "calendar", "calendario", "agenda")
    return any(marker in text for marker in delete_markers) and any(marker in text for marker in calendar_markers)


def _is_grocery_candidate(text: str) -> bool:
    grocery_markers = ("super", "supermercado", "compras", "lista")
    grocery_verbs = ("agrega", "anota", "apunta", "mete", "añade", "borra", "quita", "elimina", "saca")
    return any(marker in text for marker in grocery_markers) and any(verb in text for verb in grocery_verbs)


def _is_legal_finca_candidate(text: str) -> bool:
    markers = (
        "finca",
        "terreno",
        "abogada",
        "abogado",
        "nora",
        "registro publico",
        "documentos del caso",
        "paquete para nora",
        "caso del terreno",
    )
    return any(marker in text for marker in markers)


def _is_reminder_candidate(text: str) -> bool:
    markers = (
        "recuerdame",
        "recordarme",
        "recordatorio",
        "remind me",
    )
    return any(marker in text for marker in markers)
