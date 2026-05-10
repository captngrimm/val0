from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

def set_pending_next_action(context: ContextTypes.DEFAULT_TYPE, action: str, label: str):
    context.user_data["karen_pending_next_action"] = {
        "action": action,
        "label": label,
    }

def get_pending_next_action(context: ContextTypes.DEFAULT_TYPE):
    return context.user_data.get("karen_pending_next_action") or {}

def clear_pending_next_action(context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("karen_pending_next_action", None)

def is_confirmation(text: str) -> bool:
    t = (text or "").lower().strip()
    t = t.strip(".!¡¿? ")
    confirmations = {
        "ok",
        "okay",
        "dale",
        "si",
        "sí",
        "va",
        "vamos",
        "hagamoslo",
        "hagámoslo",
        "perfecto",
        "listo",
        "de una",
        "claro",
    }
    return t in confirmations

def document_inventory_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Sí, empezar inventario", callback_data="karen:start_document_inventory")],
        [InlineKeyboardButton("⏸️ Después", callback_data="karen:later_document_inventory")],
    ])

async def start_document_inventory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["karen_document_inventory"] = {
        "active": True,
        "step": 0,
    }

    text = (
        "Perfecto 😏📎 Empecemos el inventario de documentos.\n\n"
        "Primera pregunta:\n"
        "¿Qué documentos tienes ahora mismo del caso?\n\n"
        "Puedes responder desordenado, por ejemplo:\n"
        "- Registro Público\n"
        "- escrituras\n"
        "- fotos de papeles\n"
        "- Word/PDF\n"
        "- resúmenes\n"
        "- papeles físicos que hay que escanear"
    )

    if getattr(update, "callback_query", None):
        await update.callback_query.edit_message_text(text)
    elif update.message:
        await update.message.reply_text(text)

async def karen_next_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return

    await query.answer()

    data = query.data or ""

    if data == "karen:start_document_inventory":
        clear_pending_next_action(context)
        await start_document_inventory(update, context)
        return

    if data == "karen:later_document_inventory":
        clear_pending_next_action(context)
        await query.edit_message_text(
            "Perfecto, lo dejamos para después 😌📎\n\n"
            "Cuando quieras seguir, dime: inventario de documentos."
        )
        return

def _detect_document_categories(text: str) -> list[str]:
    t = (text or "").lower()
    found = []

    checks = [
        ("Registro Público", ("registro público", "registro publico", "finca", "folio", "inscripción", "inscripcion")),
        ("Escrituras / certificados", ("escritura", "certificado", "certificación", "certificacion")),
        ("Planos", ("plano", "planos")),
        ("Poderes / autorizaciones", ("poder", "autorización", "autorizacion")),
        ("Contratos / acuerdos", ("contrato", "acuerdo")),
        ("Fotos de documentos", ("foto", "fotos", "whatsapp", "imagen", "imágenes", "imagenes")),
        ("Word / PDF / digital", ("word", "pdf", "digital", "archivo")),
        ("Resúmenes", ("resumen", "resúmenes", "resumenes")),
        ("Papeles físicos por revisar/escanear", ("papel", "papeles", "físico", "fisico", "escanear", "escáner", "scanner")),
        ("Recibos / pagos", ("recibo", "recibos", "pago", "pagos")),
    ]

    for label, needles in checks:
        if any(n in t for n in needles):
            found.append(label)

    return found


async def maybe_handle_document_inventory(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str) -> bool:
    if not update.message:
        return False

    state = context.user_data.get("karen_document_inventory") or {}
    if not state.get("active"):
        return False

    answer = (text or "").strip()
    if not answer:
        return False

    if answer.lower().strip() in {"cancelar", "salir", "stop", "cancel"}:
        context.user_data.pop("karen_document_inventory", None)
        await update.message.reply_text("Listo. Pausé el inventario de documentos. Lo que ya guardamos queda en el caso. 📎")
        return True

    from memory_store import insert_case_note, set_active_case_id

    case_key = "KAREN-LAND-001"
    set_active_case_id(int(chat_id), case_key)

    step = int(state.get("step") or 0)

    if step == 0:
        categories = _detect_document_categories(answer)

        note_lines = [
            "Inventario inicial de documentos:",
            "",
            answer,
        ]

        if categories:
            note_lines.extend(["", "Categorías detectadas:"])
            note_lines.extend([f"- {c}" for c in categories])

        insert_case_note(
            chat_id=int(chat_id),
            case_id=case_key,
            note_text="\n".join(note_lines),
            source="document_inventory_v0",
            telegram_message_id=update.message.message_id,
        )

        context.user_data["karen_document_inventory"] = {
            "active": True,
            "step": 1,
            "last_inventory_raw": answer,
            "categories": categories,
        }

        if categories:
            cat_text = "\n".join([f"- {c}" for c in categories])
        else:
            cat_text = "- No detecté categorías claras todavía, pero guardé el texto completo."

        await update.message.reply_text(
            "Guardado ✅📎\n\n"
            "Dejé esto como inventario inicial de documentos del caso.\n\n"
            "Detecté:\n"
            f"{cat_text}\n\n"
            "Siguiente pregunta:\n"
            "¿Quién tiene esos documentos ahora mismo?\n\n"
            "Ejemplo: Karen, Frank, un familiar, abogado, Registro Público, o no sabemos todavía."
        )
        return True

    if step == 1:
        insert_case_note(
            chat_id=int(chat_id),
            case_id=case_key,
            note_text="Custodia / ubicación de documentos:\n\n" + answer,
            source="document_holder_v0",
            telegram_message_id=update.message.message_id,
        )

        context.user_data["karen_document_inventory"] = {
            "active": True,
            "step": 2,
            "document_holder_raw": answer,
            "last_inventory_raw": state.get("last_inventory_raw"),
            "categories": state.get("categories") or [],
        }

        await update.message.reply_text(
            "Guardado ✅📍\n\n"
            "Anoté quién tiene o dónde están los documentos.\n\n"
            "Siguiente pregunta:\n"
            "¿Alguno de esos documentos tiene número de finca, folio, inscripción, fecha, tomo, asiento o algún dato de Registro Público?\n\n"
            "Puedes responder: sí, no, no sé, o pegar lo que veas."
        )
        return True

    if step == 2:
        insert_case_note(
            chat_id=int(chat_id),
            case_id=case_key,
            note_text="Datos registrales / identificadores mencionados:\n\n" + answer,
            source="document_registry_details_v0",
            telegram_message_id=update.message.message_id,
        )

        context.user_data.pop("karen_document_inventory", None)

        await update.message.reply_text(
            "Guardado ✅🏛️\n\n"
            "Dejé anotados los datos registrales o la falta de ellos.\n\n"
            "Inventario documental v0 completado.\n\n"
            "Siguiente acción recomendada:\n"
            "preparar un paquete para abogado con:\n"
            "- timeline inicial\n"
            "- lista de herederos\n"
            "- documentos disponibles\n"
            "- quién tiene cada documento\n"
            "- preguntas para abogado\n\n"
            "Dime: ¿cuál es el plan? para ver dónde vamos."
        )
        return True

    return False


async def maybe_handle_pending_next_action(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> bool:
    if not update.message:
        return False

    pending = get_pending_next_action(context)
    if not pending:
        return False

    if not is_confirmation(text):
        return False

    action = pending.get("action")
    clear_pending_next_action(context)

    if action == "start_document_inventory":
        await start_document_inventory(update, context)
        return True

    return False
