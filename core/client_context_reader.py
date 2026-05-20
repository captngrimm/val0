from __future__ import annotations

from pathlib import Path
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


def render_client_idea_intake(text: str, client_id: str = "karen") -> str:
    idea = (text or "").strip()
    return (
        "💡 Idea capturada para el roadmap, Insanity.\n\n"
        f"Idea:\n{idea}\n\n"
        "La pondría tentativamente en el backlog de Valdía. "
        "Si es sobre supermercado, escuela, trabajo, agenda, recordatorios o documentos, entra perfecto en la visión de Mes 1–3.\n\n"
        "Todavía falta guardarla automáticamente en CLIENT_IDEAS, pero ya sé clasificarla como idea de roadmap."
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
        return render_client_idea_intake(text, client_id)

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
