from __future__ import annotations

import re
import unicodedata
from typing import Any


DISCOVERY_STATE_KEY = "onboarding_discovery_state"
_DISCOVERY_STAGE_CHOOSE_FLOW = "choose_flow"
_DISCOVERY_STAGE_DAILY_SOURCES = "daily_sources"
_DISCOVERY_STAGE_DAILY_RECOMMENDATION = "daily_recommendation"
_DISCOVERY_STAGE_DAILY_REVIEW_CONTENTS = "daily_review_contents"


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


def mark_onboarding_daily_recommendation_active(context: Any) -> None:
    chat_data = _onboarding_chat_data(context)
    if chat_data is not getattr(context, "chat_data", None):
        return
    chat_data[DISCOVERY_STATE_KEY] = {"stage": _DISCOVERY_STAGE_DAILY_RECOMMENDATION, "choice": "day"}


def mark_onboarding_daily_review_contents_active(context: Any) -> None:
    chat_data = _onboarding_chat_data(context)
    if chat_data is not getattr(context, "chat_data", None):
        return
    chat_data[DISCOVERY_STATE_KEY] = {"stage": _DISCOVERY_STAGE_DAILY_REVIEW_CONTENTS, "choice": "day"}


def clear_onboarding_discovery_active(context: Any) -> None:
    chat_data = _onboarding_chat_data(context)
    chat_data.pop(DISCOVERY_STATE_KEY, None)


def has_active_onboarding_discovery(context: Any) -> bool:
    state = _onboarding_chat_data(context).get(DISCOVERY_STATE_KEY)
    return isinstance(state, dict) and state.get("stage") == _DISCOVERY_STAGE_CHOOSE_FLOW


def has_active_onboarding_daily_sources(context: Any) -> bool:
    state = _onboarding_chat_data(context).get(DISCOVERY_STATE_KEY)
    return isinstance(state, dict) and state.get("stage") == _DISCOVERY_STAGE_DAILY_SOURCES


def has_active_onboarding_daily_recommendation(context: Any) -> bool:
    state = _onboarding_chat_data(context).get(DISCOVERY_STATE_KEY)
    return isinstance(state, dict) and state.get("stage") == _DISCOVERY_STAGE_DAILY_RECOMMENDATION


def has_active_onboarding_daily_review_contents(context: Any) -> bool:
    state = _onboarding_chat_data(context).get(DISCOVERY_STATE_KEY)
    return isinstance(state, dict) and state.get("stage") == _DISCOVERY_STAGE_DAILY_REVIEW_CONTENTS


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
        f"Ok, eso me dice algo importante: tus pendientes están en {source_summary}. "
        "No empezaría por documentos ni por carpetas todavía. Empezaría por Organizar mi día, "
        "porque primero necesitamos capturar lo que se te riega y convertirlo en una revisión diaria simple.\n\n"
        "Semana 1 sería sencilla:\n"
        "1. Ver dónde entran tus pendientes.\n"
        "2. Separar agenda, tareas y recordatorios.\n"
        "3. Crear una revisión diaria corta.\n"
        "4. Probar recordatorios o tareas solo cuando tú confirmes.\n"
        "5. Revisar qué realmente te ayudó antes de crecerlo.\n\n"
        "Todavía no guardé nada, no configuré nada y no creé tareas, recordatorios ni eventos de calendario. "
        "En founder beta vamos con un solo flujo primero.\n\n"
        "¿Te parece que probemos Organizar mi día como primer flujo piloto?"
    )


def classify_onboarding_recommendation_reply(text: str, *, active_context: bool = False) -> str | None:
    if not active_context:
        return None
    norm = normalize_onboarding_discovery_text(text)
    if not norm:
        return None

    cancel_markers = (
        "no",
        "mejor no",
        "cancelar",
        "cancela",
        "paremos",
        "para",
        "detente",
        "no gracias",
    )
    if norm in cancel_markers or any(marker in norm for marker in ("mejor no", "no gracias", "cancelar", "cancela")):
        return "cancel"

    pivot_choice = classify_onboarding_discovery_choice(f"quiero {norm}", active_context=True)
    if pivot_choice and pivot_choice != "day":
        return f"pivot:{pivot_choice}"

    confirm_markers = (
        "si",
        "dale",
        "correcto",
        "me parece",
        "vamos",
        "ok",
        "okay",
        "va",
        "listo",
    )
    if norm in confirm_markers or any(marker in norm for marker in ("me parece", "vamos", "dale", "correcto")):
        return "confirm"
    return None


def render_onboarding_daily_pilot_confirm_reply() -> str:
    return (
        "Perfecto. Entonces dejamos Organizar mi día como primer flujo piloto.\n\n"
        "Siguiente paso: definir qué debe traer tu revisión diaria. Para empezar, ¿quieres que incluya agenda, "
        "tareas, recordatorios, prioridades y pendientes sin fecha, o prefieres empezar más simple?\n\n"
        "Todavía no guardé ni configuré nada; solo estamos definiendo el flujo. No creé tareas, recordatorios "
        "ni eventos de calendario."
    )


def render_onboarding_recommendation_cancel_reply() -> str:
    return (
        "Perfecto, no lo forzamos. Podemos escoger otro flujo o dejarlo aquí por ahora.\n\n"
        "Todavía no guardé ni configuré nada. Si quieres, dime: documentos, clientes, pendientes, ideas u otro."
    )


def render_onboarding_pivot_reply(choice: str) -> str:
    names = {
        "documents": "documentos",
        "clients": "clientes",
        "ideas": "ideas y carpetas",
        "reminders": "pendientes y recordatorios",
        "other": "otro flujo",
    }
    name = names.get(choice, "otro flujo")
    if choice == "documents":
        opener = "Perfecto, cambiamos a documentos. No lo forzamos: si documentos es lo que te urge, empezamos ahí."
    else:
        opener = f"Perfecto, cambiamos a {name}. No lo forzamos: si eso es lo que te urge, empezamos ahí."
    return (
        f"{opener}\n\n"
        f"{render_onboarding_discovery_choice_reply(choice)}"
    )


_DAILY_REVIEW_LABELS = {
    "agenda": "agenda",
    "tasks": "tareas",
    "reminders": "recordatorios",
    "priorities": "prioridades",
    "undated": "pendientes sin fecha",
}


def classify_onboarding_daily_review_contents(text: str, *, active_context: bool = False) -> list[str] | None:
    if not active_context:
        return None
    norm = normalize_onboarding_discovery_text(text)
    if not norm:
        return None

    if any(marker in norm for marker in ("mas simple", "simple", "empezar simple")):
        return ["agenda", "tasks", "undated"]
    if norm in {"todo", "todos", "todo eso", "todos esos", "todo lo anterior"} or "todo eso" in norm:
        return ["agenda", "tasks", "reminders", "priorities", "undated"]

    selected: list[str] = []
    markers = (
        ("agenda", "agenda"),
        ("calendario", "agenda"),
        ("tarea", "tasks"),
        ("tareas", "tasks"),
        ("recordatorio", "reminders"),
        ("recordatorios", "reminders"),
        ("prioridad", "priorities"),
        ("prioridades", "priorities"),
        ("pendientes sin fecha", "undated"),
        ("sin fecha", "undated"),
    )
    for marker, key in markers:
        if marker in norm and key not in selected:
            selected.append(key)
    return selected or None


def _format_daily_review_items(keys: list[str]) -> str:
    labels = [_DAILY_REVIEW_LABELS[key] for key in keys if key in _DAILY_REVIEW_LABELS]
    if not labels:
        return "agenda, tareas importantes y pendientes sin fecha"
    if len(labels) == 1:
        return labels[0]
    return ", ".join(labels[:-1]) + " y " + labels[-1]


def render_onboarding_daily_review_contents_reply(keys: list[str]) -> str:
    simple_keys = ["agenda", "tasks", "undated"]
    is_simple = keys == simple_keys
    if is_simple:
        return (
            "Perfecto. Empezamos más simple. Yo dejaría la primera versión con solo tres cosas: agenda, "
            "tareas importantes y pendientes sin fecha.\n\n"
            "Así probamos valor rápido sin convertirlo en un monstruo. Todavía no guardé ni configuré nada, "
            "y no creé tareas, recordatorios ni eventos de calendario.\n\n"
            "¿Te parece esta versión simple para el piloto?"
        )

    items = _format_daily_review_items(keys)
    return (
        f"Perfecto. Entonces la revisión diaria piloto incluiría: {items}.\n\n"
        "La idea sería que Val te ayude a ver cada mañana qué tienes encima, qué no se puede olvidar "
        "y qué va primero.\n\n"
        "Todavía no guardé ni configuré nada; seguimos definiendo el flujo. No creé tareas, recordatorios "
        "ni eventos de calendario.\n\n"
        "¿Quieres que dejemos este diseño como propuesta para el piloto, o prefieres empezar más simple?"
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
    review_contents = classify_onboarding_daily_review_contents(
        text,
        active_context=has_active_onboarding_daily_review_contents(context),
    )
    if review_contents:
        clear_onboarding_discovery_active(context)
        await update.message.reply_text(render_onboarding_daily_review_contents_reply(review_contents))
        return True
    recommendation_reply = classify_onboarding_recommendation_reply(
        text,
        active_context=has_active_onboarding_daily_recommendation(context),
    )
    if recommendation_reply:
        if recommendation_reply == "confirm":
            mark_onboarding_daily_review_contents_active(context)
            await update.message.reply_text(render_onboarding_daily_pilot_confirm_reply())
            return True
        clear_onboarding_discovery_active(context)
        if recommendation_reply == "cancel":
            await update.message.reply_text(render_onboarding_recommendation_cancel_reply())
            return True
        if recommendation_reply.startswith("pivot:"):
            await update.message.reply_text(render_onboarding_pivot_reply(recommendation_reply.split(":", 1)[1]))
            return True
    daily_source = classify_onboarding_daily_sources_answer(
        text,
        active_context=has_active_onboarding_daily_sources(context),
    )
    if daily_source:
        mark_onboarding_daily_recommendation_active(context)
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
