from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata


@dataclass(frozen=True)
class KarenIntent:
    name: str
    confidence: float
    reason: str = ""


def _norm(text: str) -> str:
    text = (text or "").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"^[\s,.:;]*(val|valeria)[\s,.:;]+", "", text).strip()
    text = re.sub(r"\s+", " ", text)
    return text


def classify_karen_intent(text: str) -> KarenIntent:
    t = _norm(text)

    if not t:
        return KarenIntent("unknown", 0.0, "empty")

    # Agenda / due windows
    if any(x == t for x in (
        "que tengo hoy",
        "que hay hoy",
        "que debo hacer hoy",
    )):
        return KarenIntent("agenda_today", 0.95, "direct_today_agenda")

    if any(x == t for x in (
        "que tengo manana",
        "que hay manana",
        "que tengo mañana",
        "que hay mañana",
    )):
        return KarenIntent("agenda_tomorrow", 0.95, "direct_tomorrow_agenda")

    if "esta semana" in t and ("que tengo" in t or "agenda" in t or "que hay" in t):
        return KarenIntent("agenda_week", 0.9, "week_agenda")

    # Reminder list / creation
    if any(x in t for x in (
        "que recordatorios tengo",
        "mis recordatorios",
        "que tengo registrado como recordatorio",
        "que tienes registrado como recordatorio",
    )):
        return KarenIntent("reminder_list", 0.9, "reminder_list")

    if t.startswith(("recuerdame", "recuerdame", "recordarme", "recordatorio")) or "recuérdame" in t:
        return KarenIntent("reminder_create", 0.85, "reminder_create")

    # Lawyer / Nora prep
    lawyer_context = any(x in t for x in ("nora", "abogada", "abogado"))
    doc_context = any(x in t for x in (
        "documento", "documentos", "papel", "papeles",
        "paquete", "resumen", "preparar", "llevar", "llevarle",
    ))

    if lawyer_context and any(x in t for x in (
        "paquete",
        "preparame",
        "prepárame",
        "preparar",
        "prepararme",
        "prepararlos",
        "llevarle",
        "llevar",
        "ayudame a preparar",
        "ayudame a prepararme",
        "ayudame a prepararlos",
    )) and doc_context:
        return KarenIntent("prepare_lawyer", 0.92, "lawyer_doc_prep")

    if lawyer_context and any(x in t for x in (
        "que me falta",
        "que falta",
        "falta revisar",
        "falta conseguir",
        "antes de hablar",
        "pendiente revisar",
        "pendiente para",
        "pendientes para",
        "que tengo pendiente",
        "que tengo pendientes",
        "que esta pendiente",
        "que está pendiente",
        "pendiente de revisar",
        "pendientes de revisar",
    )):
        return KarenIntent("review_missing", 0.9, "lawyer_missing_review")

    # Documents
    if any(x in t for x in (
        "que documentos tengo",
        "que papeles tengo",
        "documentos registrados",
        "documentos tengo registrados",
        "que tengo registrado de documentos",
    )):
        return KarenIntent("list_documents", 0.9, "list_documents")

    if any(x in t for x in (
        "organizar documentos",
        "ordenar documentos",
        "documentos de mi caso",
        "documentos del caso",
        "papeles del caso",
        "organizar los papeles",
        "ordenar los papeles",
    )):
        return KarenIntent("organize_documents", 0.88, "organize_documents")

    # Next action
    if any(x in t for x in (
        "que hago ahora",
        "que hago primero",
        "por donde empiezo",
        "por donde empezamos",
        "siguiente paso",
        "primer paso",
    )):
        return KarenIntent("next_action", 0.8, "next_action")

    return KarenIntent("unknown", 0.0, "no_match")


if __name__ == "__main__":
    tests = [
        "Val, tengo que llevarle los documentos a la abogada, ayúdame a prepararlos.",
        "Val, qué me falta revisar antes de hablar con Nora?",
        "Val, quiero organizar los papeles del caso, por dónde empiezo?",
        "Val que tengo hoy",
        "Val, qué recordatorios tengo?",
        "Val, recuérdame mañana llamar a Nora",
        "Val, qué documentos tengo registrados?",
    ]

    for item in tests:
        intent = classify_karen_intent(item)
        print(f"{item!r} -> {intent.name} ({intent.confidence}) [{intent.reason}]")
