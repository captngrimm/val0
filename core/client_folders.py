from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FOLDER_STORE_FILENAME = "CLIENT_FOLDERS.json"
LIVE_DATA_GUARD = (
    "LIVE CLIENT DATA: text-only folder/workspace state. Do not reset, discard, "
    "or casually commit runtime changes."
)
KAREN_CLIENT_ID = "kar" + "en"


@dataclass
class FolderNote:
    text: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))


@dataclass
class ClientFolder:
    title: str
    slug: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))
    notes: list[FolderNote] = field(default_factory=list)


def _strip_accents(text: str) -> str:
    value = unicodedata.normalize("NFKD", str(text or ""))
    return "".join(ch for ch in value if not unicodedata.combining(ch))


def normalize_folder_text(text: str) -> str:
    value = _strip_accents(text).lower()
    value = re.sub(r"[¿?¡!.,;]+", " ", value)
    value = re.sub(r"\b(?:valeria|vale|val|va\s+el|bal|pal)\b", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _slugify(value: str) -> str:
    normalized = _strip_accents(value).lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return normalized or "carpeta"


def _titleize_folder(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", str(value or "")).strip(" .,:;")
    cleaned = re.sub(r"^(?:mi|mis|el|la|los|las|un|una)\s+", "", cleaned, flags=re.I).strip()
    if not cleaned:
        return ""
    words = []
    for word in cleaned.split():
        lower = word.lower()
        if lower in {"de", "del", "la", "el", "y", "para"}:
            words.append(lower)
        else:
            words.append(lower[:1].upper() + lower[1:])
    return " ".join(words)


def _capitalize_first_visible(text: str) -> str:
    value = str(text or "")
    for idx, ch in enumerate(value):
        if ch.isalpha():
            return value[:idx] + ch.upper() + value[idx + 1:]
    return value


def folder_type_emoji(title: str) -> str:
    normalized = _strip_accents(title).lower()
    if any(marker in normalized for marker in ("libro", "book", "escritura", "escribir", "novela")):
        return "📚"
    if any(marker in normalized for marker in ("supermercado", "compras", "mercado", "mandado")):
        return "🛒"
    if "idea" in normalized:
        return "💡"
    if any(marker in normalized for marker in ("legal", "abogada", "nora")):
        return "⚖️"
    return ""


def render_folder_label(folder_or_title: dict[str, Any] | str) -> str:
    title = str(folder_or_title.get("title") if isinstance(folder_or_title, dict) else folder_or_title or "Carpeta").strip()
    type_icon = folder_type_emoji(title)
    if type_icon:
        return f"{type_icon} 📁 **{title}**"
    return f"📁 **{title}**"


def client_folder_store_path(client_id: str, *, root: Path | None = None) -> Path:
    base = Path(root) if root else ROOT
    return base / "clients" / str(client_id or "").strip().lower() / FOLDER_STORE_FILENAME


def _default_store(client_id: str) -> dict[str, Any]:
    return {
        "_guard": LIVE_DATA_GUARD,
        "client_id": str(client_id or "").strip().lower(),
        "version": 1,
        "folders": [],
    }


def load_folder_store(client_id: str, *, path: Path | None = None) -> dict[str, Any]:
    store_path = Path(path) if path else client_folder_store_path(client_id)
    if not store_path.exists():
        return _default_store(client_id)
    try:
        data = json.loads(store_path.read_text(encoding="utf-8"))
    except Exception:
        return _default_store(client_id)
    if not isinstance(data, dict):
        return _default_store(client_id)
    data.setdefault("_guard", LIVE_DATA_GUARD)
    data.setdefault("client_id", str(client_id or "").strip().lower())
    data.setdefault("version", 1)
    data.setdefault("folders", [])
    if not isinstance(data["folders"], list):
        data["folders"] = []
    return data


def save_folder_store(client_id: str, store: dict[str, Any], *, path: Path | None = None) -> None:
    store_path = Path(path) if path else client_folder_store_path(client_id)
    store_path.parent.mkdir(parents=True, exist_ok=True)
    store["_guard"] = LIVE_DATA_GUARD
    store["client_id"] = str(client_id or "").strip().lower()
    store["version"] = 1
    store.setdefault("folders", [])
    tmp_path = store_path.with_suffix(store_path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(store, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp_path.replace(store_path)


def _find_folder(store: dict[str, Any], name: str) -> dict[str, Any] | None:
    slug = _slugify(name)
    for folder in store.get("folders", []):
        if not isinstance(folder, dict):
            continue
        if str(folder.get("slug") or "") == slug:
            return folder
    return None


def create_folder(client_id: str, name: str, *, path: Path | None = None) -> tuple[dict[str, Any], bool]:
    title = _titleize_folder(name)
    if not title:
        raise ValueError("Folder title is required.")
    store = load_folder_store(client_id, path=path)
    existing = _find_folder(store, title)
    if existing:
        return existing, False
    folder = {
        "title": title,
        "slug": _slugify(title),
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "notes": [],
    }
    store.setdefault("folders", []).append(folder)
    save_folder_store(client_id, store, path=path)
    return folder, True


def add_folder_note(client_id: str, folder_name: str, note_text: str, *, path: Path | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    folder, _created = create_folder(client_id, folder_name, path=path)
    note = {
        "text": re.sub(r"\s+", " ", str(note_text or "")).strip(),
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    if not note["text"]:
        raise ValueError("Note text is required.")
    store = load_folder_store(client_id, path=path)
    stored_folder = _find_folder(store, folder["title"])
    if stored_folder is None:
        stored_folder = folder
        store.setdefault("folders", []).append(stored_folder)
    stored_folder.setdefault("notes", []).append(note)
    save_folder_store(client_id, store, path=path)
    return stored_folder, note


def list_folders(client_id: str, *, path: Path | None = None) -> list[dict[str, Any]]:
    store = load_folder_store(client_id, path=path)
    return [folder for folder in store.get("folders", []) if isinstance(folder, dict)]


def get_folder(client_id: str, name: str, *, path: Path | None = None) -> dict[str, Any] | None:
    store = load_folder_store(client_id, path=path)
    return _find_folder(store, name)


def _extract_create_folder_name(text: str) -> str:
    raw = re.sub(r"^\s*(?:valeria|vale|val|va\s+el|bal|pal)[,\s]+", "", str(text or ""), flags=re.I).strip()
    patterns = [
        r"crea(?:me)?\s+(?:una\s+)?carpeta\s+(?:para\s+)?(.+)$",
        r"crear\s+(?:una\s+)?carpeta\s+(?:para\s+)?(.+)$",
    ]
    for pattern in patterns:
        match = re.search(pattern, raw, flags=re.I)
        if match:
            return _titleize_folder(match.group(1))
    return ""


def _extract_open_folder_name(text: str) -> str:
    raw = re.sub(r"^\s*(?:valeria|vale|val|va\s+el|bal|pal)[,\s]+", "", str(text or ""), flags=re.I).strip()
    match = re.search(r"abre\s+(?:mi\s+)?carpeta\s+(.+)$", raw, flags=re.I)
    return _titleize_folder(match.group(1)) if match else ""


def _extract_folder_note(text: str) -> tuple[str, str]:
    raw = re.sub(r"^\s*(?:valeria|vale|val|va\s+el|bal|pal)[,\s]+", "", str(text or ""), flags=re.I).strip()
    match = re.search(r"guarda\s+(?:esta\s+)?(?:idea|nota)\s+en\s+([^:]+):\s*(.+)$", raw, flags=re.I | re.S)
    if not match:
        return "", ""
    return _titleize_folder(match.group(1)), re.sub(r"\s+", " ", match.group(2)).strip()


def _extract_folder_contents_name(text: str) -> str:
    raw = re.sub(r"^\s*(?:valeria|vale|val|va\s+el|bal|pal)[,\s]+", "", str(text or ""), flags=re.I).strip()
    match = re.search(r"(?:que|qué)\s+tengo\s+en\s+(.+?)(?:\?|$)", raw, flags=re.I)
    return _titleize_folder(match.group(1)) if match else ""


def classify_folder_command(text: str) -> tuple[str, dict[str, str]]:
    norm = normalize_folder_text(text)
    if not norm:
        return "", {}
    note_folder, note_text = _extract_folder_note(text)
    if note_folder and note_text:
        return "save_note", {"folder": note_folder, "text": note_text}
    create_name = _extract_create_folder_name(text)
    if create_name:
        return "create", {"folder": create_name}
    if any(marker in norm for marker in ("lista mis carpetas", "listar mis carpetas", "que carpetas tengo", "qué carpetas tengo", "mis carpetas")):
        return "list", {}
    open_name = _extract_open_folder_name(text)
    if open_name:
        return "open", {"folder": open_name}
    contents_name = _extract_folder_contents_name(text)
    if contents_name:
        return "contents", {"folder": contents_name}
    return "", {}


def render_folder_list(client_id: str, *, path: Path | None = None) -> str:
    folders = list_folders(client_id, path=path)
    if not folders:
        return (
            'Tany, todavía no tengo carpetas guardadas.\n\n'
            'Puedes decir: "Val, crea carpeta Libro".'
        )
    lines = ["Tany, estas son tus carpetas:", ""]
    for idx, folder in enumerate(folders, start=1):
        notes = folder.get("notes") if isinstance(folder.get("notes"), list) else []
        lines.append(f"{idx}. {render_folder_label(folder)} · {len(notes)} nota(s)")
    return "\n".join(lines)


def render_folder_view(folder: dict[str, Any]) -> str:
    notes = folder.get("notes") if isinstance(folder.get("notes"), list) else []
    title = str(folder.get("title") or "Carpeta")
    label = render_folder_label(folder)
    lines = [
        f"Tany, abrí tu carpeta {label}.",
        "",
        "📁 Estado rápido",
        f"- {len(notes)} nota(s) guardada(s).",
        "- Text-only por ahora: no moví documentos, tareas ni calendario.",
        "",
        "Puedes decir:",
        f'1. "Val, guarda esta idea en {title}: ..."',
        f'2. "Val, qué tengo en {title}?"',
    ]
    return "\n".join(lines)


def render_folder_contents(folder: dict[str, Any]) -> str:
    title = str(folder.get("title") or "Carpeta")
    label = render_folder_label(folder)
    notes = folder.get("notes") if isinstance(folder.get("notes"), list) else []
    lines = [f"Tany, esto tengo en {label}:", ""]
    if not notes:
        lines.append("1. Todavía no hay notas guardadas.")
    else:
        for idx, note in enumerate(notes, start=1):
            lines.append(f"{idx}. {_capitalize_first_visible(note.get('text', '').strip())}")
    return "\n".join(lines).strip()


async def maybe_handle_client_folder_query(update: Any, context: Any, chat_id: int, client_id: str, text: str, *, store_path: Path | None = None) -> bool:
    if not update or not getattr(update, "message", None):
        return False
    if str(client_id or "").strip().lower() not in {KAREN_CLIENT_ID, "client-zero"}:
        return False
    action, fields = classify_folder_command(text)
    if not action:
        return False
    runtime_client_id = KAREN_CLIENT_ID if str(client_id or "").strip().lower() == "client-zero" else str(client_id).strip().lower()
    if action == "create":
        folder, created = create_folder(runtime_client_id, fields["folder"], path=store_path)
        label = render_folder_label(folder)
        if created:
            await update.message.reply_text(f"Tany, listo. Creé la carpeta {label}.")
        else:
            await update.message.reply_text(f"Tany, ya tenía la carpeta {label}. La dejé como estaba.")
        return True
    if action == "list":
        await update.message.reply_text(render_folder_list(runtime_client_id, path=store_path))
        return True
    if action == "open":
        folder = get_folder(runtime_client_id, fields["folder"], path=store_path)
        if not folder:
            await update.message.reply_text(
                f"Tany, no encuentro la carpeta {fields['folder']} todavía. "
                f'Puedes crearla con: "Val, crea carpeta {fields["folder"]}".'
            )
            return True
        await update.message.reply_text(render_folder_view(folder))
        return True
    if action == "save_note":
        folder, note = add_folder_note(runtime_client_id, fields["folder"], fields["text"], path=store_path)
        await update.message.reply_text(f"Tany, guardé esa idea en {render_folder_label(folder)}: {_capitalize_first_visible(note['text'])}")
        return True
    if action == "contents":
        folder = get_folder(runtime_client_id, fields["folder"], path=store_path)
        if not folder:
            await update.message.reply_text(
                f"Tany, no encuentro la carpeta {fields['folder']} todavía. "
                f'Puedes crearla con: "Val, crea carpeta {fields["folder"]}".'
            )
            return True
        await update.message.reply_text(render_folder_contents(folder))
        return True
    return False
