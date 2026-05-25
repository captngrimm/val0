import re
import unicodedata


def _normalize(text: str) -> str:
    norm = unicodedata.normalize("NFKD", (text or "").lower())
    norm = "".join(ch for ch in norm if not unicodedata.combining(ch))
    norm = re.sub(r"[¿?¡!.,:;]+", " ", norm)
    norm = re.sub(r"\s+", " ", norm).strip()
    norm = re.sub(r"^(val|valeria|vale)\s+", "", norm).strip()
    return norm


def looks_like_karen_meeting_prep_request(text: str) -> bool:
    norm = _normalize(text)

    prep_markers = (
        "preparame para hablar",
        "preparame para la reunion",
        "preparame para reunion",
        "preparame para reunirme",
        "ayudame a prepararme para hablar",
        "ayudame a prepararme para la reunion",
        "ayudame a preparar la reunion",
        "prepara la reunion",
        "preparar la reunion",
    )
    meeting_context = (
        "abogada",
        "abogado",
        "nora",
        "advisor",
        "asesor",
        "asesora",
    )

    return any(marker in norm for marker in prep_markers) and any(marker in norm for marker in meeting_context)


def render_karen_meeting_prep_checklist(text: str = "") -> str:
    norm = _normalize(text)
    person = "la abogada"
    if "advisor" in norm:
        person = "el advisor"
    elif "asesor" in norm:
        person = "el asesor"
    elif "asesora" in norm:
        person = "la asesora"
    elif "nora" in norm:
        person = "Nora"
    elif "abogado" in norm and "abogada" not in norm:
        person = "el abogado"

    return (
        f"🧾 Prep para hablar con {person}\n\n"
        "1. Objetivo de la reunión:\n"
        "   Confirmar el próximo paso y qué documentos faltan revisar/presentar.\n\n"
        "2. Documentos a tener a mano:\n"
        "   - documentos con texto leído/indexado\n"
        "   - documentos pendientes de OCR/revisión\n"
        "   - cualquier resumen o cronología disponible\n\n"
        "3. Preguntas sugeridas:\n"
        "   - ¿Cuál es el estado actual del caso?\n"
        "   - ¿Qué documento falta revisar o conseguir?\n"
        "   - ¿Qué fecha o plazo debemos cuidar?\n"
        "   - ¿Cuál es el próximo paso concreto?\n\n"
        "4. Pendiente antes de la reunión:\n"
        "   Preparar preguntas y confirmar qué documentos llevará Karen.\n\n"
        "Límite: esto organiza la preparación; no sustituye criterio legal o profesional."
    )
