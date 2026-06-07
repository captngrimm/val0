from __future__ import annotations

import re
import unicodedata
from typing import Any


def _strip_accents(text: str) -> str:
    value = unicodedata.normalize("NFKD", str(text or ""))
    return "".join(ch for ch in value if not unicodedata.combining(ch))


def normalize_onboarding_discovery_text(text: str) -> str:
    value = _strip_accents(text).lower()
    value = re.sub(r"[¿?¡!.,:;]+", " ", value)
    value = re.sub(r"\b(?:valeria|vale|val|va\s+el|bal|pal)\b", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def is_onboarding_discovery_query(text: str) -> bool:
    norm = normalize_onboarding_discovery_text(text)
    if not norm:
        return False

    exact_or_near = (
        "como me puedes ayudar",
        "como puedes ayudarme",
        "que puedes hacer",
        "que sabes hacer",
        "ayudame a empezar",
        "ayudame a escoger por donde empezar",
        "no se que necesito",
        "que me recomiendas",
        "por donde empiezo",
    )
    if any(marker in norm for marker in exact_or_near):
        return True

    if "ayudame" in norm and "empezar" in norm:
        return True
    if "no se" in norm and "necesito" in norm:
        return True
    return False


def render_onboarding_discovery_reply(*, client_id: str | None = None) -> str:
    return (
        "Puedo ayudarte como operadora personal por Telegram, pero lo útil no es tirarte un menú gigante. "
        "Empezamos con un flujo primero: una cosa concreta que quieras ordenar ahora.\n\n"
        "Ejemplos concretos:\n"
        "1. Organizar mi día: agenda, tareas y prioridades.\n"
        "2. Pendientes/recordatorios: que no se te pierdan compromisos.\n"
        "3. Documentos/casos: ordenar papeles, resumir con cautela y preparar preguntas.\n"
        "4. Clientes/seguimiento: próximas acciones, promesas y follow-up.\n"
        "5. Ideas/carpetas: guardar notas, proyectos o ideas sin regarlas.\n\n"
        "Límite founder beta: no soy IA mágica, no hago autonomía completa y no reemplazo abogado, médico, contador "
        "ni criterio humano. Tú controlas qué se guarda y qué acciones se confirman.\n\n"
        "Para empezar bien, escogemos un solo flujo primero. ¿Por dónde empezamos: organizar tu día, pendientes, "
        "documentos, clientes, ideas o algo diferente?"
    )


async def maybe_handle_onboarding_discovery(update: Any, context: Any, chat_id: int, client_id: str, text: str) -> bool:
    if not update or not getattr(update, "message", None):
        return False
    if not is_onboarding_discovery_query(text):
        return False
    await update.message.reply_text(render_onboarding_discovery_reply(client_id=client_id))
    return True
