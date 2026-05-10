from telegram import Update
from telegram.ext import ContextTypes

CASE_KEY = "KAREN-LAND-001"

def render_lawyer_package(chat_id: int) -> str:
    from core.karen_case_status import render_karen_case_status

    case_status = render_karen_case_status(int(chat_id))

    return (
        "⚖️📦 Paquete inicial para abogado — caso del terreno familiar\n\n"
        "Este paquete es para llegar a la cita con orden, no para reemplazar criterio legal. "
        "Val organiza hechos, documentos y preguntas; el abogado interpreta y define estrategia. 😌\n\n"
        "Resumen base:\n\n"
        f"{case_status}\n\n"
        "📌 Preguntas clave para abrir la cita:\n"
        "1. ¿Cuál es el estado legal actual del terreno según estos datos?\n"
        "2. ¿Qué documentos faltan para hacer una revisión seria?\n"
        "3. ¿Qué debe verificarse primero en Registro Público?\n"
        "4. ¿Qué necesita firmar o aprobar cada heredero?\n"
        "5. ¿Qué pasa si un heredero no coopera?\n"
        "6. ¿Qué puede adelantar la familia antes de contratar o avanzar más?\n"
        "7. ¿Cuál sería el primer paso legal/práctico después de revisar documentos?\n"
        "8. ¿Qué costos y tiempos iniciales debemos esperar?\n\n"
        "📎 Checklist para antes de la cita:\n"
        "- Revisar fotos de documentos.\n"
        "- Buscar finca, folio, inscripción, tomo, asiento o fecha.\n"
        "- Separar documentos por tipo: Registro Público, resúmenes, fotos, físicos.\n"
        "- Confirmar quién tiene originales o copias.\n"
        "- Llevar lista de los cinco herederos.\n"
        "- Anotar qué eventos desde 1986 están confirmados y cuáles son aproximados.\n\n"
        "Siguiente acción recomendada:\n"
        "Mandarle esto a Karen y revisar juntas qué dato falta antes de llamar al abogado. 😏"
    )

async def karen_lawyer_package_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    chat_id = update.effective_chat.id
    await update.message.reply_text(render_lawyer_package(int(chat_id)))

async def maybe_handle_karen_lawyer_package(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> bool:
    if not update.message:
        return False

    t = (text or "").lower().strip()

    markers = (
        "prepara paquete para abogado",
        "preparar paquete para abogado",
        "paquete para abogado",
        "hazme el paquete para abogado",
        "armar paquete para abogado",
        "armemos paquete para abogado",
        "resumen para abogado",
        "prepara resumen para abogado",
    )

    if any(m in t for m in markers):
        chat_id = update.effective_chat.id
        await update.message.reply_text(render_lawyer_package(int(chat_id)))
        return True

    return False
