from telegram import Update
from telegram.ext import ContextTypes

CASE_KEY = "KAREN-LAND-001"

def question(step: int) -> str:
    qs = {
        0: "Primera pregunta 😏\n\n¿Cómo quieres llamar este caso?\n\nEjemplo: Terreno familiar, Caso del terreno, Trámite de la familia.",
        1: "Perfecto. Ahora la gente del arroz con mango familiar 🧠📁\n\n¿Quiénes son los herederos o personas principales involucradas?",
        2: "Vamos al timeline.\n\n¿Cuál es el evento más antiguo que recuerdas del caso?\nSi no recuerdas exacto, dime aproximado.",
        3: "Ahora documentos 📎\n\n¿Qué documentos tienen o saben que existen?\nRegistro Público, escritura, certificado, plano, poder, contrato, recibo, foto, Word, PDF.\n\n¿Están físicos, digitales, fotos de WhatsApp o mezclados como gaveta de cables?",
        4: "Última pregunta de arranque, prometido, no soy notaría con WiFi 😌\n\n¿Ya hay alguna cita, fecha límite o urgencia esta semana?\n\nEjemplo: cita con abogado, documento que pedir, reunión familiar, llamada pendiente.",
    }
    return qs.get(step, "")

async def interrogate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    chat_id = update.effective_chat.id if update.effective_chat else 0

    from memory_store import upsert_case, set_active_case_id, insert_case_note

    row_id = upsert_case(
        chat_id=int(chat_id),
        expediente=CASE_KEY,
        client_name="Karen",
        client_alias="terreno familiar",
    )
    set_active_case_id(int(chat_id), CASE_KEY)

    insert_case_note(
        chat_id=int(chat_id),
        case_id=CASE_KEY,
        note_text="Interrogator v0 iniciado para caso de terreno familiar.",
        source="interrogator",
    )

    context.user_data["karen_interrogator"] = {
        "active": True,
        "step": 0,
        "case_key": CASE_KEY,
        "case_row_id": int(row_id),
    }

    await update.message.reply_text(
        "🕵️‍♀️ Interrogator v0 activado.\n\n"
        "Vamos a construir la memoria del caso paso a paso.\n"
        "No tienes que contarlo perfecto ni en orden. Si algo es aproximado, lo marcamos así. "
        "Si no está confirmado, lo dejamos como por verificar.\n\n"
        + question(0)
    )

async def maybe_handle_karen_interrogator(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str) -> bool:
    if not update.message:
        return False

    state = context.user_data.get("karen_interrogator") or {}
    if not state.get("active"):
        return False

    answer = (text or "").strip()
    if not answer:
        return False

    if answer.lower().strip() in {"cancelar", "salir", "stop", "cancel"}:
        context.user_data.pop("karen_interrogator", None)
        await update.message.reply_text("Listo. Pausé el Interrogator. No perdimos lo ya guardado. 🧠")
        return True

    step = int(state.get("step") or 0)
    case_key = str(state.get("case_key") or CASE_KEY)
    case_row_id = int(state.get("case_row_id") or 0)

    from memory_store import insert_case_note, insert_case_event, insert_task, set_active_case_id

    set_active_case_id(int(chat_id), case_key)

    labels = {
        0: "Nombre del caso",
        1: "Personas/herederos involucrados",
        2: "Evento más antiguo recordado",
        3: "Documentos disponibles",
        4: "Cita, fecha límite o urgencia de esta semana",
    }

    label = labels.get(step, f"Respuesta paso {step}")
    note_text = f"{label}: {answer}"

    insert_case_note(
        chat_id=int(chat_id),
        case_id=case_key,
        note_text=note_text,
        source=f"interrogator_step_{step}",
        telegram_message_id=update.message.message_id,
    )

    if step == 2 and case_row_id:
        try:
            insert_case_event(
                chat_id=int(chat_id),
                case_id=int(case_row_id),
                event_text=answer,
                raw_text=answer,
            )
        except Exception:
            pass

    if step == 4:
        try:
            insert_task(
                chat_id=int(chat_id),
                case_id=case_key,
                task_text=answer,
                source="interrogator",
                priority="high",
            )
        except Exception:
            pass

    next_step = step + 1

    if next_step <= 4:
        state["step"] = next_step
        context.user_data["karen_interrogator"] = state
        await update.message.reply_text(
            f"Guardado ✅\n\n"
            f"Anoté: {label}.\n\n"
            f"{question(next_step)}"
        )
        return True

    context.user_data.pop("karen_interrogator", None)

    await update.message.reply_text(
        "Listo, Insanity 🧠📁\n\n"
        "Ya tengo el arranque del caso:\n"
        "- nombre/contexto del caso\n"
        "- personas principales\n"
        "- primer evento del timeline\n"
        "- documentos disponibles\n"
        "- urgencia o cita de esta semana\n\n"
        "Te propongo este plan inicial:\n\n"
        "1. Armar el timeline base desde 1986 hasta hoy.\n"
        "2. Hacer inventario de documentos: Registro Público, resúmenes y papeles físicos.\n"
        "3. Marcar qué documentos faltan, cuáles hay que escanear y quién los tiene.\n"
        "4. Preparar preguntas para abogado.\n"
        "5. Programar las citas con abogados para la próxima semana.\n"
        "6. Después de cada cita, registrar nuevas acciones, fechas y responsables.\n\n"
        "Primera acción recomendada:\n"
        "Preparar un paquete simple para el abogado con timeline inicial + documentos disponibles + preguntas clave.\n\n"
        "Está rudo, sí. Pero ya dejó de ser humo en abanico. 😌\n\n"
        "Siguiente paso sugerido:\n"
        "Dime: armemos preguntas para el abogado."
    )
    return True
