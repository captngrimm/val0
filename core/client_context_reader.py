from __future__ import annotations

from pathlib import Path
from datetime import datetime
import re
import unicodedata


BASE_DIR = Path(__file__).resolve().parent.parent
CLIENTS_DIR = BASE_DIR / "clients"


def _norm(text: str) -> str:
    text = (text or "").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"^[\s,.:;]*(val|valeria)[\s,.:;]+", "", text).strip()
    text = re.sub(r"\s+", " ", text)
    return text


def _read_client_file(client_id: str, filename: str) -> str:
    safe_client = re.sub(r"[^a-zA-Z0-9_-]", "", client_id or "")
    path = CLIENTS_DIR / safe_client / filename
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def load_client_context(client_id: str) -> dict:
    return {
        "profile": _read_client_file(client_id, "CLIENT_PROFILE.md"),
        "roadmap": _read_client_file(client_id, "CLIENT_ROADMAP.md"),
        "ideas": _read_client_file(client_id, "CLIENT_IDEAS.md"),
        "status": _read_client_file(client_id, "CLIENT_STATUS.md"),
        "grocery": _read_client_file(client_id, "CLIENT_GROCERY.md"),
    }


def classify_client_context_query(text: str) -> str:
    t = _norm(text)

    if not t:
        return "unknown"

    if any(x in t for x in (
        "que puedes hacer hoy",
        "qué puedes hacer hoy",
        "que puedes hacer",
        "qué puedes hacer",
        "que haces hoy",
        "qué haces hoy",
        "capacidades",
        "que sabes hacer",
        "qué sabes hacer",
    )):
        return "capabilities_today"

    if any(x in t for x in (
        "que viene despues",
        "qué viene después",
        "que sigue",
        "qué sigue",
        "roadmap",
        "proximo paso",
        "próximo paso",
        "siguiente paso",
        "mes 1",
        "mes 2",
        "mes 3",
    )):
        return "roadmap"

    if any(x in t for x in (
        "estamos a tiempo",
        "vamos a tiempo",
        "como vamos",
        "cómo vamos",
        "estado del proyecto",
        "estatus del proyecto",
        "status del proyecto",
    )):
        return "status"

    if any(x in t for x in (
        "que ideas tengo",
        "qué ideas tengo",
        "ideas guardadas",
        "ideas capturadas",
        "lista de ideas",
        "backlog de ideas",
        "que ideas hay",
        "qué ideas hay",
    )):
        return "idea_list"

    if (
        any(x in t for x in ("borra", "elimina", "quita", "saca"))
        and any(x in t for x in ("super", "súper", "supermercado", "compras", "lista"))
    ):
        return "grocery_delete"

    if any(x in t for x in (
        "que tengo en la lista del super",
        "qué tengo en la lista del súper",
        "que tengo en la lista del súper",
        "lista del super",
        "lista del súper",
        "lista de super",
        "lista de súper",
        "lista supermercado",
        "lista del supermercado",
        "que hay en la lista de compras",
        "qué hay en la lista de compras",
    )):
        return "grocery_list"

    if (
        any(x in t for x in ("anota", "apunta", "agrega", "añade", "mete"))
        and any(x in t for x in ("super", "súper", "supermercado", "compras", "lista"))
    ):
        return "grocery_add"

    if any(x in t for x in (
        "tengo una idea",
        "se me ocurrio",
        "se me ocurrió",
        "idea para val",
        "agrega esta idea",
        "podrias ayudarme con",
        "podrías ayudarme con",
    )):
        return "idea_intake"

    return "unknown"


def render_client_capabilities_today(client_id: str = "karen") -> str:
    ctx = load_client_context(client_id)
    status = ctx.get("status", "")
    roadmap = ctx.get("roadmap", "")

    return (
        "🧭✨ Hoy puedo ayudarte con esto, Insanity:\n\n"
        "1. Caso/finca/legal\n"
        "- Preparar el paquete para Nora.\n"
        "- Revisar qué falta antes de hablar con la abogada.\n"
        "- Organizar documentos y papeles del caso.\n\n"
        "2. Agenda y recordatorios básicos\n"
        "- Revisar qué tienes hoy, mañana o esta semana si está registrado.\n"
        "- Crear recordatorios cuando me das fecha/hora clara.\n\n"
        "3. Roadmap de Val Personal\n"
        "- Decirte qué está listo.\n"
        "- Decirte qué viene después.\n"
        "- Capturar ideas para mejorar Val.\n\n"
        "Todavía no soy ChatGPT completo con tacones y café, pero ya estoy aprendiendo a operar tu mundo por partes. 😌"
    )


def render_client_roadmap(client_id: str = "karen") -> str:
    return (
        "🗺️ Roadmap Val Personal / Karen\n\n"
        "Antes del 25 de mayo:\n"
        "- Estabilizar caso/finca/legal.\n"
        "- Mejorar voz e intención natural.\n"
        "- Mantener recordatorios y agenda básica.\n"
        "- Reducir respuestas tipo menú Atari.\n\n"
        "Mes 1:\n"
        "- Val te ayuda a no perder cosas: documentos, eventos, recordatorios, agenda básica e ideas.\n\n"
        "Mes 2:\n"
        "- Más áreas: escuela, supermercado, trabajo, familia y pendientes personales.\n\n"
        "Mes 3:\n"
        "- Seguimiento antes/después de citas. Ejemplo: después de hablar con Nora, Val te pregunta qué pasó y guarda contexto.\n\n"
        "Mes 4-6:\n"
        "- Conversación más natural dentro de tu mundo, con memoria estructurada lista para crecer.\n\n"
        "La meta no es que hables como robot. La meta es que Val entienda intención y use las herramientas correctas."
    )


def render_client_status(client_id: str = "karen") -> str:
    return (
        "📍 Estado actual Val Personal / Karen\n\n"
        "Estamos en founder-beta / client-zero personal.\n\n"
        "Ya sellado:\n"
        "- Paquete para Nora.\n"
        "- Checklist de faltantes.\n"
        "- Carpeta Clara para organizar documentos.\n"
        "- Router natural v0 para entender intención legal/documental.\n"
        "- Estructura CLIENT_* para perfil, roadmap, ideas y estado.\n\n"
        "Vamos bien para el objetivo actual: que Val sea útil en el caso y empiece a expandirse como operadora personal.\n\n"
        "Límites actuales:\n"
        "- No es ChatGPT completo todavía.\n"
        "- OCR/fotos aún no está completo.\n"
        "- Algunas rutas siguen siendo determinísticas.\n\n"
        "Siguiente construcción recomendada: empezar captura simple de supermercado/listas y seguimiento básico de pendientes personales."
    )


def _extract_idea_text(text: str) -> str:
    raw = (text or "").strip()
    cleaned = re.sub(
        r"(?is)^\s*(val|valeria)?[\s,.:;]*(tengo una idea|se me ocurrio|se me ocurrió|idea para val|agrega esta idea)\s*[:,-]*\s*",
        "",
        raw,
    ).strip()
    return cleaned or raw


def append_client_idea(client_id: str, text: str, source: str = "telegram") -> bool:
    """Append a roadmap idea to CLIENT_IDEAS.md. Controlled local persistence v0."""
    safe_client = re.sub(r"[^a-zA-Z0-9_-]", "", client_id or "")
    if not safe_client:
        return False

    idea = _extract_idea_text(text)
    if not idea or len(idea) < 4:
        return False

    path = CLIENTS_DIR / safe_client / "CLIENT_IDEAS.md"
    if not path.exists():
        return False

    existing = path.read_text(encoding="utf-8")

    # Lightweight dedupe guard:
    # do not append the exact same normalized idea again if already captured.
    if f"  - idea: {idea}\n" in existing:
        return True

    now = datetime.now().isoformat(timespec="seconds")
    entry = (
        "\n\n## Captured ideas\n"
        if "## Captured ideas" not in existing
        else "\n"
    )
    entry += (
        f"- [{now}] source={source}\n"
        f"  - raw: {text.strip()}\n"
        f"  - idea: {idea}\n"
        f"  - status: open/admin-review\n"
    )

    with path.open("a", encoding="utf-8") as f:
        f.write(entry)

    return True


def render_client_ideas_list(client_id: str = "karen") -> str:
    ctx = load_client_context(client_id)
    ideas = ctx.get("ideas", "").strip()

    if not ideas:
        return "💡 No encontré ideas guardadas todavía, Insanity."

    # Keep v0 simple/readable: return the ideas file with a short intro.
    return (
        "💡 Ideas guardadas para el roadmap de Val Personal:\n\n"
        f"{ideas}\n\n"
        "Estas ideas son backlog: no significan promesa automática, pero sí quedan visibles para revisión y priorización."
    )


def render_client_idea_intake(text: str, client_id: str = "karen", persist: bool = False) -> str:
    idea = _extract_idea_text(text)
    saved = False
    if persist:
        saved = append_client_idea(client_id, text, source="telegram")

    save_line = (
        "La dejé guardada en el backlog para revisión. 🧷"
        if saved
        else "La clasifico como idea de roadmap; si quieres, luego la dejamos guardada en el backlog."
    )

    return (
        "💡 Idea capturada para el roadmap, Insanity.\n\n"
        f"Idea:\n{idea}\n\n"
        "La pondría tentativamente en el backlog de Val Personal. "
        "Si es sobre supermercado, escuela, trabajo, agenda, recordatorios o documentos, entra perfecto en la visión de Mes 1–3.\n\n"
        f"{save_line}"
    )



def _extract_grocery_items(text: str) -> list[str]:
    raw = (text or "").strip()

    cleaned = re.sub(
        r"(?is)^\s*(val|valeria)?[\s,.:;]*(anota|apunta|agrega|añade|mete)\s*",
        "",
        raw,
    ).strip()

    # Remove trailing destination/context phrases before splitting items.
    # Handles: "para el súper", "para super", "en la lista de compras", etc.
    cleaned = re.sub(
        r"(?is)\s*(para|en|a)\s+(el|la)?\s*(super|súper|supermercado|lista de compras|lista)\s*[.!?¡¿]*\s*$",
        "",
        cleaned,
    ).strip()

    cleaned = re.sub(r"(?i)\s+y\s+", ", ", cleaned)
    parts = [x.strip(" .;-") for x in cleaned.split(",")]
    return [x for x in parts if len(x) >= 2]


def _ensure_grocery_file(client_id: str = "karen") -> Path | None:
    safe_client = re.sub(r"[^a-zA-Z0-9_-]", "", client_id or "")
    if not safe_client:
        return None

    client_dir = CLIENTS_DIR / safe_client
    if not client_dir.exists():
        return None

    path = client_dir / "CLIENT_GROCERY.md"
    if not path.exists():
        path.write_text(
            "# CLIENT_GROCERY — Karen / Val Personal\n\n"
            "## Current list\n\n"
            "_No hay productos guardados todavía._\n",
            encoding="utf-8",
        )
    return path


def append_client_grocery_items(client_id: str, text: str, source: str = "telegram") -> tuple[bool, list[str]]:
    path = _ensure_grocery_file(client_id)
    if path is None:
        return False, []

    items = _extract_grocery_items(text)
    if not items:
        return False, []

    existing = path.read_text(encoding="utf-8")
    existing_norm = _norm(existing)

    # If this is the first real item, remove placeholder.
    existing = existing.replace("_No hay productos guardados todavía._\n", "")

    added: list[str] = []
    for item in items:
        line = f"- {item}"
        if _norm(line) in existing_norm:
            continue
        added.append(item)
        existing += f"{line}\n"

    if added:
        path.write_text(existing.rstrip() + "\n", encoding="utf-8")

    return True, added


def render_client_grocery_add(text: str, client_id: str = "karen", persist: bool = True) -> str:
    items = _extract_grocery_items(text)
    if not items:
        return (
            "🛒 Te entendí que quieres anotar algo para el súper, Insanity, "
            "pero no vi productos claros. Prueba: “Val, anota arroz, leche y jabón para el súper.”"
        )

    saved = False
    added: list[str] = []
    if persist:
        saved, added = append_client_grocery_items(client_id, text, source="telegram")

    shown = added if added else items
    bullets = "\n".join(f"- {x}" for x in shown)

    if saved:
        return (
            "🛒 Listo, Insanity. Lo anoté para el súper:\n\n"
            f"{bullets}\n\n"
            "Cuando quieras revisar, dime: “Val, ¿qué tengo en la lista del súper?”"
        )

    return (
        "🛒 Lo clasifiqué como lista de súper:\n\n"
        f"{bullets}\n\n"
        "Pero no pude guardarlo todavía. Qué dramática la tecnología, pero por lo menos no lo inventé. 😌"
    )



def _extract_grocery_delete_items(text: str) -> list[str]:
    raw = (text or "").strip()

    # Only extract delete targets when the phrase actually starts like a delete command.
    # Supports:
    # - "Val, borra pan de la lista del súper"
    # - "Vale, borra pan"
    # - "quitar leche"
    # - "elimina café"
    match = re.match(
        r"(?is)^\s*(?:val|vale|valeria)?[\s,.:;]*(?:quitar|quita|borrar|borra|eliminar|elimina|sacar|saca)\b\s*(.+?)\s*$",
        raw,
    )
    if not match:
        return []

    cleaned = match.group(1).strip()

    cleaned = re.sub(
        r"(?is)\s*(?:de|del|en|a|para)\s+(?:la\s+)?(?:lista\s+)?(?:del\s+)?(?:super|súper|supermercado|compras|lista)\s*[.!?¡¿]*\s*$",
        "",
        cleaned,
    ).strip()

    cleaned = re.sub(r"(?i)\s+y\s+", ", ", cleaned)
    parts = [x.strip(" .;-") for x in cleaned.split(",")]
    return [x for x in parts if len(x) >= 2]


def delete_client_grocery_items(client_id: str, text: str) -> tuple[bool, list[str], list[str]]:
    path = _ensure_grocery_file(client_id)
    if path is None:
        return False, [], []

    targets = _extract_grocery_delete_items(text)
    if not targets:
        return False, [], []

    original = path.read_text(encoding="utf-8")
    lines = original.splitlines()

    removed: list[str] = []
    kept_lines: list[str] = []

    target_norms = {_norm(x) for x in targets}

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- "):
            item = stripped[2:].strip()
            if _norm(item) in target_norms:
                removed.append(item)
                continue
        kept_lines.append(line)

    if removed:
        # If no list items remain, restore placeholder.
        has_items = any(x.strip().startswith("- ") for x in kept_lines)
        new_text = "\n".join(kept_lines).rstrip() + "\n"
        if not has_items:
            new_text = (
                "# CLIENT_GROCERY — Karen / Val Personal\n\n"
                "## Current list\n\n"
                "_No hay productos guardados todavía._\n"
            )
        path.write_text(new_text, encoding="utf-8")

    missing = [x for x in targets if _norm(x) not in {_norm(r) for r in removed}]
    return bool(removed), removed, missing


def render_client_grocery_delete(text: str, client_id: str = "karen", persist: bool = True) -> str:
    targets = _extract_grocery_delete_items(text)
    if not targets:
        return (
            "🛒 Te entendí que quieres borrar algo de la lista, Insanity, "
            "pero no vi qué producto. Prueba: “Val, borra leche de la lista del súper.”"
        )

    removed: list[str] = []
    missing: list[str] = []

    if persist:
        ok, removed, missing = delete_client_grocery_items(client_id, text)
    else:
        ok = True
        removed = targets
        missing = []

    if removed:
        bullets = "\n".join(f"- {x}" for x in removed)
        msg = "🛒 Listo, Insanity. Quité de la lista:\n\n" + bullets
        if missing:
            msg += "\n\nNo encontré esto para borrar:\n" + "\n".join(f"- {x}" for x in missing)
        return msg

    return (
        "🛒 Revisé la lista, Insanity, pero no encontré eso para borrar:\n\n"
        + "\n".join(f"- {x}" for x in targets)
    )



def render_client_grocery_list(client_id: str = "karen") -> str:
    path = _ensure_grocery_file(client_id)
    if path is None:
        return "🛒 No encontré archivo de lista de súper para este cliente todavía."

    grocery = path.read_text(encoding="utf-8").strip()
    lines = [
        line for line in grocery.splitlines()
        if line.strip().startswith("- ")
    ]

    if not lines:
        return "🛒 Tu lista de súper está vacía por ahora, Insanity."

    return (
        "🛒 Lista de súper guardada, Insanity:\n\n"
        + "\n".join(lines)
        + "\n\nPor ahora puedo guardar y mostrar la lista. Borrar/editar viene después, sin ponerse intensa todavía. 😌"
    )



def render_client_context_answer(text: str, client_id: str = "karen", persist_ideas: bool = True) -> str | None:
    qtype = classify_client_context_query(text)

    if qtype == "capabilities_today":
        return render_client_capabilities_today(client_id)
    if qtype == "roadmap":
        return render_client_roadmap(client_id)
    if qtype == "status":
        return render_client_status(client_id)
    if qtype == "idea_list":
        return render_client_ideas_list(client_id)
    if qtype == "grocery_delete":
        return render_client_grocery_delete(text, client_id, persist=persist_ideas)
    if qtype == "grocery_list":
        return render_client_grocery_list(client_id)
    if qtype == "grocery_add":
        return render_client_grocery_add(text, client_id, persist=persist_ideas)
    if qtype == "idea_intake":
        return render_client_idea_intake(text, client_id, persist=persist_ideas)

    return None


if __name__ == "__main__":
    tests = [
        "Val, qué puedes hacer hoy?",
        "Val, qué viene después?",
        "Val, estamos a tiempo?",
        "Val, tengo una idea: que me ayudes con supermercado.",
        "Val, qué ideas tengo guardadas?",
        "Val, anota arroz, leche y jabón para el súper.",
        "Val, qué tengo en la lista del súper?",
        "Val, borra leche de la lista del súper.",
        "Val, dime cualquier cosa random",
    ]

    for t in tests:
        q = classify_client_context_query(t)
        ans = render_client_context_answer(t, "karen", persist_ideas=False)
        print(f"{t!r} -> {q} -> {'ANSWER' if ans else 'NO_ANSWER'}")

    print("extract_idea:", _extract_idea_text("Val, tengo una idea: que me ayudes con supermercado."))
