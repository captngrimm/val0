import re
from telegram import Update
from telegram.ext import ContextTypes
from core.karen_voice import saved_case_intro, consultative_next_step

CASE_KEY = "KAREN-LAND-001"


def _norm(text: str) -> str:
    text = (text or "").lower()
    text = text.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
    return re.sub(r"\s+", " ", text).strip()


def extract_karen_case_facts(text: str) -> dict:
    raw = text or ""
    compact = re.sub(r"\s+", "", raw)

    facts = {}

    # Handles both "Finca 10082" and pasted-table garbage like "Finca10082Tomo/Rollo316Folio308"
    m = re.search(r"finca\s*[:#]?\s*(\d{3,})", raw, flags=re.I)
    if not m:
        m = re.search(r"Finca(\d{3,})", compact, flags=re.I)
    if m:
        facts["finca"] = m.group(1)

    m = re.search(r"(?:tomo\s*/\s*rollo|tomo|rollo)\s*[:#]?\s*(\d+)", raw, flags=re.I)
    if not m:
        m = re.search(r"(?:Tomo/Rollo|Tomo|Rollo)(\d+)", compact, flags=re.I)
    if m:
        facts["tomo_rollo"] = m.group(1)

    m = re.search(r"folio\s*[:#]?\s*(\d+)", raw, flags=re.I)
    if not m:
        m = re.search(r"Folio(\d+)", compact, flags=re.I)
    if m:
        facts["folio"] = m.group(1)

    m = re.search(r"propietario original\s*[:\-]?\s*([A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ ]{3,80})", raw, flags=re.I)
    if not m:
        m = re.search(r"Propietariooriginal([A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ]+(?:[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ]+)?)", compact)
    if m:
        val = m.group(1).strip()
        # Fix compact "EufemioMontenegro" if needed.
        val = re.sub(r"(?<=[a-záéíóúñ])(?=[A-ZÁÉÍÓÚÑ])", " ", val)
        facts["propietario_original"] = val

    m = re.search(r"tipo de proceso\s*[:\-]?\s*([A-Za-zÁÉÍÓÚÑáéíóúñ ]{4,80})", raw, flags=re.I)
    if not m:
        m = re.search(r"Tipodeproceso([A-Za-zÁÉÍÓÚÑáéíóúñ]+)", compact)
    if m:
        val = m.group(1).strip()
        val = re.sub(r"(?<=[a-záéíóúñ])(?=[A-ZÁÉÍÓÚÑ])", " ", val)
        facts["tipo_proceso"] = val

    m = re.search(r"fecha de fallecimiento\s*[:\-]?\s*([0-9]{1,2}\s+de\s+[A-Za-zÁÉÍÓÚÑáéíóúñ]+\s+de\s+[0-9]{4})", raw, flags=re.I)
    if not m:
        m = re.search(r"Fechadefallecimiento([0-9]{1,2}de[A-Za-zÁÉÍÓÚÑáéíóúñ]+de[0-9]{4})", compact)
    if m:
        val = m.group(1).replace("de", " de ") if "de" not in m.group(1).split() else m.group(1)
        val = re.sub(r"\s+", " ", val).strip()
        facts["fecha_fallecimiento"] = val

    m = re.search(r"escritura pública\s*(?:no\.?|número|numero)?\s*[:#]?\s*(\d+)", raw, flags=re.I)
    if not m:
        m = re.search(r"EscrituraP[úu]blicaNo\.?(\d+)", compact, flags=re.I)
    if m:
        facts["escritura_publica"] = m.group(1)

    m = re.search(r"fecha de escritura\s*[:\-]?\s*([0-9]{1,2}\s+de\s+[A-Za-zÁÉÍÓÚÑáéíóúñ]+\s+de\s+[0-9]{4})", raw, flags=re.I)
    if not m:
        m = re.search(r"Fechadeescritura([0-9]{1,2}de[A-Za-zÁÉÍÓÚÑáéíóúñ]+de[0-9]{4})", compact)
    if m:
        val = m.group(1).replace("de", " de ") if "de" not in m.group(1).split() else m.group(1)
        val = re.sub(r"\s+", " ", val).strip()
        facts["fecha_escritura"] = val

    if "notaría sexta" in raw.lower() or "notaria sexta" in raw.lower() or "NotaríaSexta" in compact:
        facts["notaria"] = "Notaría Sexta del Circuito de Panamá (La Chorrera)"

    heirs = []
    known_heirs = [
        "Carmen Montenegro de Sandino",
        "Javier Morán Montenegro Ortega",
        "Odilia Montenegro de Estribí",
        "Teonila Antonia Montenegro de Cruz",
        "Martina Montenegro de Martínez",
    ]
    low_raw = raw.lower()
    low_compact = compact.lower()
    for h in known_heirs:
        if h.lower() in low_raw or h.replace(" ", "").lower() in low_compact:
            heirs.append(h)
    if heirs:
        facts["herederos"] = heirs

    return facts


def save_karen_case_facts(chat_id: int, text: str, telegram_message_id=None) -> dict:
    facts = extract_karen_case_facts(text)
    if not facts:
        return {}

    from memory_store import insert_case_note, set_active_case_id

    set_active_case_id(int(chat_id), CASE_KEY)

    lines = ["Datos básicos de la finca / caso:"]
    if facts.get("finca"):
        lines.append(f"Finca: {facts['finca']}")
    if facts.get("tomo_rollo"):
        lines.append(f"Tomo/Rollo: {facts['tomo_rollo']}")
    if facts.get("folio"):
        lines.append(f"Folio: {facts['folio']}")
    if facts.get("propietario_original"):
        lines.append(f"Propietario original: {facts['propietario_original']}")
    if facts.get("tipo_proceso"):
        lines.append(f"Tipo de proceso: {facts['tipo_proceso']}")
    if facts.get("fecha_fallecimiento"):
        lines.append(f"Fecha de fallecimiento: {facts['fecha_fallecimiento']}")
    if facts.get("escritura_publica"):
        lines.append(f"Escritura Pública: No. {facts['escritura_publica']}")
    if facts.get("fecha_escritura"):
        lines.append(f"Fecha de escritura: {facts['fecha_escritura']}")
    if facts.get("notaria"):
        lines.append(f"Notaría: {facts['notaria']}")
    if facts.get("herederos"):
        lines.append("Herederos declarados:")
        lines.extend([f"- {h}" for h in facts["herederos"]])

    insert_case_note(
        chat_id=int(chat_id),
        case_id=CASE_KEY,
        note_text="\n".join(lines),
        source="case_facts_v0",
        telegram_message_id=telegram_message_id,
    )

    return facts


def load_karen_case_facts(chat_id: int) -> dict:
    from memory_store import fetch_case_notes

    notes = fetch_case_notes(int(chat_id), CASE_KEY, limit=120)
    merged = {}

    for n in notes:
        if str(n.get("source") or "") != "case_facts_v0":
            continue
        raw = str(n.get("note_text") or "")
        facts = extract_karen_case_facts(raw)
        for k, v in facts.items():
            if v:
                merged[k] = v

    return merged


def render_case_facts(facts: dict, mode: str = "all", chat_id: int | None = None) -> str:
    if not facts:
        return (
            "Todavía no tengo datos básicos suficientes de la finca guardados 😕📁\n\n"
            "Pásame datos como finca, tomo/rollo, folio, propietario original o herederos, y los dejo asociados al caso."
        )

    if mode == "finca":
        parts = []
        if facts.get("finca"):
            parts.append(f"Finca: {facts['finca']}")
        if facts.get("tomo_rollo"):
            parts.append(f"Tomo/Rollo: {facts['tomo_rollo']}")
        if facts.get("folio"):
            parts.append(f"Folio: {facts['folio']}")
        if parts:
            return "📌 Datos de finca que tengo guardados:\n\n" + "\n".join([f"- {p}" for p in parts])
        return "Tengo datos del caso, pero todavía no veo número de finca/tomo/folio guardado."

    if mode == "heirs":
        heirs = facts.get("herederos") or []
        if heirs:
            return "👥 Herederos declarados que tengo guardados:\n\n" + "\n".join([f"- {h}" for h in heirs])
        return "Todavía no tengo la lista de herederos guardada con suficiente claridad."

    lines = [saved_case_intro(chat_id), ""]
    labels = [
        ("finca", "Finca"),
        ("tomo_rollo", "Tomo/Rollo"),
        ("folio", "Folio"),
        ("propietario_original", "Propietario original"),
        ("tipo_proceso", "Tipo de proceso"),
        ("fecha_fallecimiento", "Fecha de fallecimiento"),
        ("escritura_publica", "Escritura Pública No."),
        ("fecha_escritura", "Fecha de escritura"),
        ("notaria", "Notaría"),
    ]
    for key, label in labels:
        if facts.get(key):
            lines.append(f"- {label}: {facts[key]}")

    if facts.get("herederos"):
        lines.append("")
        lines.append("Herederos declarados:")
        lines.extend([f"- {h}" for h in facts["herederos"]])

    lines.append("")
    lines.append(consultative_next_step("abogado"))
    return "\n".join(lines)


async def maybe_handle_karen_case_facts(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> bool:
    if not update.message:
        return False

    chat_id = update.effective_chat.id
    t = _norm(text)

    # If the user pasted obvious case facts, save them BEFORE trying to answer.
    # Otherwise a pasted block containing "Finca" can be mistaken for a query and return "no data".
    incoming_facts = extract_karen_case_facts(text)
    incoming_is_strong = bool(
        incoming_facts.get("finca")
        and (
            incoming_facts.get("folio")
            or incoming_facts.get("tomo_rollo")
            or incoming_facts.get("herederos")
        )
    )

    if incoming_is_strong:
        save_karen_case_facts(
            int(chat_id),
            text,
            telegram_message_id=update.message.message_id,
        )
        await update.message.reply_text(
            "Guardé los datos básicos del caso ✅📁\n\n"
            f"{render_case_facts(incoming_facts, mode='all', chat_id=int(chat_id))}"
        )
        return True

    facts = load_karen_case_facts(int(chat_id))

    finca_markers = (
        "numero de finca",
        "número de finca",
        "dame la finca",
        "cual es la finca",
        "cuál es la finca",
        "finca relacionada",
        "datos de la finca",
        "tomo",
        "folio",
    )
    heirs_markers = (
        "quienes son los herederos",
        "quiénes son los herederos",
        "herederos declarados",
        "lista de herederos",
    )
    basics_markers = (
        "datos basicos del caso",
        "datos básicos del caso",
        "que datos basicos tienes del caso",
        "qué datos básicos tienes del caso",
        "que datos basicos tienes",
        "qué datos básicos tienes",
        "informacion basica del caso",
        "información básica del caso",
        "que informacion basica tienes",
        "qué información básica tienes",
        "que datos tienes del caso",
        "qué datos tienes del caso",
        "que tienes guardado de la finca",
        "qué tienes guardado de la finca",
        "tienes en memoria informacion basica",
        "tienes en memoria información básica",
    )

    summary_blockers = (
        "resume",
        "resumen",
        "qué dicen los documentos",
        "que dicen los documentos",
        "busca",
        "buscar",
        "menciona",
        "dónde sale",
        "donde sale",
    )

    if (
        any(m in t for m in finca_markers)
        and not any(b in t for b in summary_blockers)
    ):
        await update.message.reply_text(
            render_case_facts(
                facts,
                mode="finca",
                chat_id=int(chat_id)
            )
        )
        return True

    if any(m in t for m in heirs_markers):
        await update.message.reply_text(render_case_facts(facts, mode="heirs", chat_id=int(chat_id)))
        return True

    if any(m in t for m in basics_markers):
        await update.message.reply_text(render_case_facts(facts, mode="all", chat_id=int(chat_id)))
        return True

    return False


async def maybe_capture_karen_case_facts(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str) -> bool:
    """
    Passive capture: if a user pastes obvious land-case registry facts, save them
    without stealing the whole conversation unless enough facts are detected.
    """
    if not update.message:
        return False

    facts = save_karen_case_facts(
        int(chat_id),
        text,
        telegram_message_id=update.message.message_id,
    )

    # Only consume if strong enough; otherwise let normal pipeline continue.
    strong = bool(facts.get("finca") and (facts.get("folio") or facts.get("tomo_rollo") or facts.get("herederos")))

    if strong:
        await update.message.reply_text(
            "Guardé datos básicos del caso ✅📁\n\n"
            f"{render_case_facts(facts, mode='all', chat_id=int(chat_id))}"
        )
        return True

    return False
