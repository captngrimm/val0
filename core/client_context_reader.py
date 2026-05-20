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
        "3. Roadmap de Valdía\n"
        "- Decirte qué está listo.\n"
        "- Decirte qué viene después.\n"
        "- Capturar ideas para mejorar Val.\n\n"
        "Todavía no soy ChatGPT completo con tacones y café, pero ya estoy aprendiendo a operar tu mundo por partes. 😌"
    )


def render_client_roadmap(client_id: str = "karen") -> str:
    return (
        "🗺️ Roadmap Valdía / Karen\n\n"
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
        "📍 Estado actual Valdía / Karen\n\n"
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
        "Siguiente construcción recomendada: que Val lea este contexto y pueda contestar roadmap, estado e ideas sin inventar."
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
        "La pondría tentativamente en el backlog de Valdía. "
        "Si es sobre supermercado, escuela, trabajo, agenda, recordatorios o documentos, entra perfecto en la visión de Mes 1–3.\n\n"
        f"{save_line}"
    )


def render_client_context_answer(text: str, client_id: str = "karen") -> str | None:
    qtype = classify_client_context_query(text)

    if qtype == "capabilities_today":
        return render_client_capabilities_today(client_id)
    if qtype == "roadmap":
        return render_client_roadmap(client_id)
    if qtype == "status":
        return render_client_status(client_id)
    if qtype == "idea_intake":
        return render_client_idea_intake(text, client_id, persist=True)

    return None


if __name__ == "__main__":
    tests = [
        "Val, qué puedes hacer hoy?",
        "Val, qué viene después?",
        "Val, estamos a tiempo?",
        "Val, tengo una idea: que me ayudes con supermercado.",
        "Val, dime cualquier cosa random",
    ]

    for t in tests:
        q = classify_client_context_query(t)
        ans = render_client_context_answer(t, "karen")
        print(f"{t!r} -> {q} -> {'ANSWER' if ans else 'NO_ANSWER'}")

    print("extract_idea:", _extract_idea_text("Val, tengo una idea: que me ayudes con supermercado."))
