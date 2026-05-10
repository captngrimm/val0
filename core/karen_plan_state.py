from telegram import Update
from telegram.ext import ContextTypes

PLAN_ID = "karen_landops_mvp"
CASE_KEY = "KAREN-LAND-001"

PLAN_PHASES = [
    "Intake inicial del caso",
    "Timeline base 1986-presente",
    "Inventario de documentos",
    "Preguntas para abogado",
    "Citas con abogados",
    "Acciones post-cita",
]

def render_plan_status() -> str:
    return (
        "🧭 Plan activo: Karen LandOps MVP\n\n"
        "Objetivo:\n"
        "Organizar el trámite familiar del terreno como memoria viva: timeline, documentos, pendientes, citas y preguntas para abogado.\n\n"
        "Estado actual:\n"
        "✅ Fase 1: Intake inicial del caso — completada en versión ruda.\n"
        "➡️ Fase actual: preparar preguntas para abogado + empezar inventario de documentos.\n\n"
        "Ya tengo:\n"
        "- Nombre/contexto del caso\n"
        "- Personas principales / herederos\n"
        "- Primer evento del timeline desde 1986\n"
        "- Documentos mencionados: Registro Público, resúmenes y papeles físicos\n"
        "- Urgencia: programar citas con abogados para la próxima semana\n\n"
        "Falta:\n"
        "1. Armar timeline base desde 1986 hasta hoy.\n"
        "2. Hacer inventario detallado de documentos.\n"
        "3. Marcar qué falta, qué hay que escanear y quién tiene cada cosa.\n"
        "4. Preparar preguntas para abogado.\n"
        "5. Registrar citas y acciones nuevas después de cada reunión.\n\n"
        "Siguiente acción recomendada:\n"
        "Dime: armemos preguntas para el abogado. 😏"
    )

async def karen_plan_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    await update.message.reply_text(render_plan_status())

async def maybe_handle_karen_plan_query(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> bool:
    if not update.message:
        return False

    t = (text or "").lower().strip()
    markers = (
        "cual es el plan",
        "cuál es el plan",
        "donde vamos",
        "dónde vamos",
        "que falta",
        "qué falta",
        "como va el caso",
        "cómo va el caso",
        "como va el caso del terreno",
        "cómo va el caso del terreno",
        "plan del terreno",
        "estado del plan",
        "dame el plan",
    )

    if any(m in t for m in markers):
        await update.message.reply_text(render_plan_status())
        return True

    return False
