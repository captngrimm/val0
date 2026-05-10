from telegram import Update
from telegram.ext import ContextTypes
from core.karen_next_action import set_pending_next_action

CASE_KEY = "KAREN-LAND-001"

LAWYER_QUESTIONS_TEXT = """⚖️ Preguntas para el abogado — caso del terreno familiar

Ok, Insanity 🧠📁
Para la primera cita, yo llevaría preguntas claras. No vamos a llegar con “ay abogado, ilumíneme” como si fuera misa legal. 😌

1. Estado legal del terreno
- ¿Cuál es el estado actual del terreno según la información disponible?
- ¿Qué habría que verificar primero para saber si el trámite puede avanzar?
- ¿Hay algún riesgo legal evidente por el tiempo que lleva el caso?

2. Herederos y participación familiar
- Si son cinco herederos, ¿qué necesita firmar o aprobar cada uno?
- ¿Qué pasa si uno de los herederos no coopera o no responde?
- ¿Se necesita poder, autorización o representación formal de alguien?

3. Documentos necesarios
- ¿Qué documentos son indispensables para revisar el caso?
- ¿Qué documentos del Registro Público debemos pedir o actualizar?
- ¿Sirven fotos/copias o se necesitan originales/certificados?
- ¿Qué documentos faltan para poder tomar una decisión seria?

4. Timeline y hechos desde 1986
- ¿Qué importancia tienen los eventos desde 1986?
- ¿Qué hechos deberíamos ordenar primero en una línea de tiempo?
- ¿Qué fechas deben estar confirmadas y cuáles pueden quedar como aproximadas?

5. Registro Público / instituciones
- ¿Qué exactamente debemos buscar o verificar en el Registro Público?
- ¿Hay que revisar finca, folio, inscripción, propietario actual o historial?
- ¿Qué otra institución puede ser necesaria: notaría, municipio, ANATI, juzgado?

6. Próximas acciones
- ¿Cuál sería el primer paso legal/práctico después de revisar los documentos?
- ¿Qué puede hacerse esta semana?
- ¿Qué acciones dependen del abogado y cuáles puede adelantar la familia?

7. Costos, tiempos y riesgos
- ¿Cuánto podría tardar la primera revisión seria?
- ¿Qué costos iniciales debemos esperar?
- ¿Cuáles son los principales riesgos o bloqueos?
- ¿Qué resultado realista podemos esperar en el corto plazo?

Primera tarea recomendada:
Antes de la cita, armar un paquete simple con:
- resumen corto del caso
- timeline inicial desde 1986
- lista de herederos
- documentos disponibles
- documentos faltantes o por confirmar

Dime: guardemos estas preguntas en el caso.
"""

async def karen_lawyer_questions_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    await update.message.reply_text(LAWYER_QUESTIONS_TEXT)

async def maybe_handle_karen_lawyer_questions(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> bool:
    if not update.message:
        return False

    t = (text or "").lower().strip()

    save_markers = (
        "guardemos estas preguntas en el caso",
        "guarda estas preguntas en el caso",
        "guardar estas preguntas en el caso",
        "guarda las preguntas en el caso",
        "guardar las preguntas en el caso",
        "guardemos las preguntas en el caso",
        "guardar preguntas en el caso",
        "guarda preguntas en el caso",
        "deja estas preguntas en el caso",
        "deja las preguntas en el caso",
        "mete estas preguntas en el caso",
        "mete las preguntas en el caso",
    )

    if any(m in t for m in save_markers):
        from memory_store import insert_case_note, set_active_case_id

        chat_id = int(update.effective_chat.id)
        set_active_case_id(chat_id, CASE_KEY)

        insert_case_note(
            chat_id=chat_id,
            case_id=CASE_KEY,
            note_text="Preguntas para abogado registradas:\n\n" + LAWYER_QUESTIONS_TEXT,
            source="lawyer_questions_v0",
            telegram_message_id=update.message.message_id,
        )

        set_pending_next_action(
            context,
            action="start_document_inventory",
            label="inventario de documentos",
        )

        await update.message.reply_text(
            "Guardado ✅📁\n\n"
            "Dejé las preguntas para el abogado dentro del caso del terreno.\n\n"
            "Siguiente paso recomendado:\n"
            "hacer inventario de documentos.\n\n"
            "¿Seguimos con eso ahora? Responde OK y arrancamos."
        )
        return True

    markers = (
        "armemos preguntas para el abogado",
        "preguntas para el abogado",
        "que le preguntamos al abogado",
        "qué le preguntamos al abogado",
        "que preguntarle al abogado",
        "qué preguntarle al abogado",
        "preparar cita con abogado",
        "preparar preguntas abogado",
    )

    if any(m in t for m in markers):
        await update.message.reply_text(LAWYER_QUESTIONS_TEXT)
        return True

    return False
