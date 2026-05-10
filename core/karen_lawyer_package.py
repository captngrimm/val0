from telegram import Update
from telegram.ext import ContextTypes

CASE_KEY = "KAREN-LAND-001"

def render_lawyer_package(chat_id: int) -> str:
    """
    Compact attorney-facing package for Karen LandOps.

    This intentionally does not embed /karencase directly.
    /karencase is operator status.
    /lawyerpackage is meeting prep.
    """
    return (
        "⚖️📦 Paquete inicial para abogado — caso del terreno familiar\n\n"
        "Nota: este resumen organiza información para la cita. No reemplaza revisión legal. "
        "El abogado debe verificar documentos, estado registral y estrategia. 😌\n\n"

        "1. Resumen corto del caso\n"
        "- Se trata de un trámite/disputa familiar sobre un terreno.\n"
        "- Hay cinco herederos involucrados: A, B, C, D y E.\n"
        "- Karen y Frank están ayudando a organizar la información.\n"
        "- El trámite tiene antecedentes desde 1986. Algunas fechas/eventos aún deben confirmarse.\n\n"

        "2. Objetivo de la cita\n"
        "- Entender el estado legal actual del terreno.\n"
        "- Confirmar qué documentos faltan o deben actualizarse.\n"
        "- Saber qué puede adelantar la familia antes del siguiente paso legal.\n"
        "- Definir acciones, responsables y fechas después de la cita.\n\n"

        "3. Documentos disponibles o mencionados\n"
        "- Documentos del Registro Público.\n"
        "- Resúmenes en Word.\n"
        "- Fotos de papeles enviadas por WhatsApp.\n"
        "- Papeles físicos que hay que revisar o escanear.\n\n"

        "4. Quién tiene documentos\n"
        "- Karen tiene algunos documentos.\n"
        "- Frank tiene fotos por WhatsApp.\n"
        "- Un familiar tiene papeles físicos que deben revisarse o escanearse.\n\n"

        "5. Datos pendientes de verificar\n"
        "- Finca.\n"
        "- Folio.\n"
        "- Inscripción.\n"
        "- Fecha.\n"
        "- Tomo.\n"
        "- Asiento.\n"
        "- Propietario actual / historial registral, si aplica.\n\n"

        "6. Preguntas clave para el abogado\n"
        "1. ¿Cuál es el estado legal actual del terreno con la información disponible?\n"
        "2. ¿Qué debe verificarse primero en Registro Público?\n"
        "3. ¿Qué documentos son indispensables para hacer una revisión seria?\n"
        "4. ¿Sirven copias/fotos o se necesitan originales/certificados?\n"
        "5. ¿Qué necesita firmar o aprobar cada heredero?\n"
        "6. ¿Qué pasa si un heredero no coopera o no responde?\n"
        "7. ¿Hay algún riesgo por el tiempo transcurrido desde 1986?\n"
        "8. ¿Cuál es el primer paso práctico después de revisar los documentos?\n"
        "9. ¿Qué puede adelantar la familia esta semana?\n"
        "10. ¿Qué costos y tiempos iniciales debemos esperar?\n\n"

        "7. Checklist antes de llamar o reunirse\n"
        "- Revisar fotos de documentos y separar las legibles de las borrosas.\n"
        "- Buscar finca, folio, inscripción, tomo, asiento o fecha.\n"
        "- Escanear o fotografiar papeles físicos con buena luz.\n"
        "- Confirmar quién tiene originales y quién tiene copias.\n"
        "- Llevar lista de los cinco herederos.\n"
        "- Marcar qué datos están confirmados y cuáles son aproximados.\n\n"

        "8. Siguiente acción recomendada\n"
        "Preparar una carpeta simple para el abogado con:\n"
        "- este resumen\n"
        "- timeline inicial desde 1986\n"
        "- lista de herederos\n"
        "- documentos disponibles\n"
        "- documentos pendientes por conseguir/verificar\n\n"

        "Listo. Esto ya se puede usar como guía de reunión sin llegar como pollo sin cabeza. 😏"
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
