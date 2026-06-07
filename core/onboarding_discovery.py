from __future__ import annotations

import re
import unicodedata
from typing import Any


DISCOVERY_STATE_KEY = "onboarding_discovery_state"
_DISCOVERY_STAGE_CHOOSE_FLOW = "choose_flow"
_DISCOVERY_STAGE_DAILY_SOURCES = "daily_sources"


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


def _onboarding_chat_data(context: Any) -> dict[str, Any]:
    chat_data = getattr(context, "chat_data", None)
    if isinstance(chat_data, dict):
        return chat_data
    return {}


def mark_onboarding_discovery_active(context: Any) -> None:
    chat_data = _onboarding_chat_data(context)
    if chat_data is not getattr(context, "chat_data", None):
        return
    chat_data[DISCOVERY_STATE_KEY] = {"stage": _DISCOVERY_STAGE_CHOOSE_FLOW}


def mark_onboarding_daily_sources_active(context: Any) -> None:
    chat_data = _onboarding_chat_data(context)
    if chat_data is not getattr(context, "chat_data", None):
        return
    chat_data[DISCOVERY_STATE_KEY] = {"stage": _DISCOVERY_STAGE_DAILY_SOURCES, "choice": "day"}


def clear_onboarding_discovery_active(context: Any) -> None:
    chat_data = _onboarding_chat_data(context)
    chat_data.pop(DISCOVERY_STATE_KEY, None)


def has_active_onboarding_discovery(context: Any) -> bool:
    state = _onboarding_chat_data(context).get(DISCOVERY_STATE_KEY)
    return isinstance(state, dict) and state.get("stage") == _DISCOVERY_STAGE_CHOOSE_FLOW


def has_active_onboarding_daily_sources(context: Any) -> bool:
    state = _onboarding_chat_data(context).get(DISCOVERY_STATE_KEY)
    return isinstance(state, dict) and state.get("stage") == _DISCOVERY_STAGE_DAILY_SOURCES


def _has_direct_discovery_choice_intent(norm: str) -> bool:
    markers = (
        "empezar por",
        "empecemos por",
        "empecemos con",
        "quiero empezar",
        "quiero ordenar",
        "me gustaria ordenar",
        "me gustaria empezar",
        "escojo",
        "elijo",
        "ayudame con",
        "ayudame a ordenar",
    )
    return any(marker in norm for marker in markers)


def classify_onboarding_discovery_choice(text: str, *, active_context: bool = False) -> str | None:
    norm = normalize_onboarding_discovery_text(text)
    if not norm:
        return None

    direct_choice = active_context or _has_direct_discovery_choice_intent(norm)
    if not direct_choice:
        return None

    if any(marker in norm for marker in ("otro", "otra cosa", "diferente", "algo diferente")):
        return "other"

    if any(marker in norm for marker in ("pendiente", "pendientes", "recordatorio", "recordatorios")):
        return "reminders"

    if any(marker in norm for marker in ("documento", "documentos", "caso", "casos", "papel", "papeles")):
        return "documents"

    if any(marker in norm for marker in ("cliente", "clientes", "seguimiento", "follow up", "followup")):
        return "clients"

    if any(marker in norm for marker in ("idea", "ideas", "carpeta", "carpetas")):
        return "ideas"

    if any(marker in norm for marker in ("organizar mi dia", "mi dia", "agenda", "dia")):
        return "day"

    return None


def render_onboarding_discovery_choice_reply(choice: str) -> str:
    replies = {
        "day": (
            "Perfecto. Empezamos por organizar tu día. ¿Dónde tienes tus pendientes ahora: calendario, WhatsApp, "
            "notas, papel o en la cabeza?"
        ),
        "reminders": (
            "Perfecto. Empezamos por pendientes y recordatorios. ¿Qué tipo de cosas se te pierden más: fechas, "
            "pagos, llamadas, tareas pequeñas o promesas a otras personas?"
        ),
        "documents": (
            "Perfecto. Empezamos por documentos. ¿Qué quieres ordenar primero: documentos personales, un caso, "
            "contratos, recibos o algo administrativo?"
        ),
        "clients": (
            "Perfecto. Empezamos por seguimiento. ¿A quién o qué tienes que perseguir más: clientes, proveedores, "
            "oportunidades, cobros o tareas internas?"
        ),
        "ideas": (
            "Perfecto. Empezamos por ideas y carpetas. ¿Qué quieres guardar sin que se pierda: ideas de negocio, "
            "libro, proyectos, pendientes o notas sueltas?"
        ),
        "other": "Perfecto. Dime en una frase qué te gustaría ordenar o que Val te ayude a no perder.",
    }
    body = replies.get(choice)
    if not body:
        body = replies["other"]
    return (
        f"{body}\n\n"
        "En founder beta lo armamos paso a paso: un solo flujo primero. Todavía no guardo nada ni creo acciones."
    )


def classify_onboarding_daily_sources_answer(text: str, *, active_context: bool = False) -> str | None:
    if not active_context:
        return None
    norm = normalize_onboarding_discovery_text(text)
    if not norm:
        return None

    broad_sources = (
        ("calendario", "calendario"),
        ("whatsapp", "WhatsApp"),
        ("notas", "notas"),
        ("nota", "notas"),
        ("papel", "papel"),
        ("papeles", "papel"),
        ("cabeza", "tu cabeza"),
        ("mente", "tu cabeza"),
    )
    found: list[str] = []
    for marker, label in broad_sources:
        if marker in norm and label not in found:
            found.append(label)

    scattered_markers = (
        "todo regado",
        "todos lados",
        "en todos lados",
        "regados",
        "regadas",
        "por todos lados",
        "desordenado",
        "desordenados",
    )
    if any(marker in norm for marker in scattered_markers):
        if found:
            return ", ".join(found) + " y otros lugares"
        return "varios lugares"

    if len(found) >= 2:
        return ", ".join(found[:-1]) + " y " + found[-1]
    if found:
        return found[0]
    return None


def render_onboarding_daily_recommendation_reply(source_summary: str) -> str:
    return (
        f"Perfecto. Entonces entiendo que tus pendientes están en {source_summary}. "
        "Mi recomendación: empezamos con el flujo Organizar mi día.\n\n"
        "Semana 1 sería simple:\n"
        "1. Identificar dónde entran tus pendientes.\n"
        "2. Separar agenda, tareas y recordatorios.\n"
        "3. Armar una revisión diaria corta.\n"
        "4. Probar recordatorios o tareas solo después de confirmarlo.\n"
        "5. Revisar qué sí te ayudó antes de crecerlo.\n\n"
        "Todavía no guardé nada, no configuré nada y no creé tareas, recordatorios ni eventos de calendario. "
        "En founder beta vamos con un solo flujo primero.\n\n"
        "¿Quieres que usemos este como tu primer flujo piloto?"
    )


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
    daily_source = classify_onboarding_daily_sources_answer(
        text,
        active_context=has_active_onboarding_daily_sources(context),
    )
    if daily_source:
        clear_onboarding_discovery_active(context)
        await update.message.reply_text(render_onboarding_daily_recommendation_reply(daily_source))
        return True
    active_choice_context = has_active_onboarding_discovery(context)
    choice = classify_onboarding_discovery_choice(text, active_context=active_choice_context)
    if choice:
        if choice == "day":
            mark_onboarding_daily_sources_active(context)
        else:
            clear_onboarding_discovery_active(context)
        await update.message.reply_text(render_onboarding_discovery_choice_reply(choice))
        return True
    if not is_onboarding_discovery_query(text):
        return False
    mark_onboarding_discovery_active(context)
    await update.message.reply_text(render_onboarding_discovery_reply(client_id=client_id))
    return True
