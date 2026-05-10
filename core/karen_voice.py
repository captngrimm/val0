def get_karen_display_name(chat_id: int | None = None) -> str:
    """
    Best-effort display name for Karen client-zero flow.
    Falls back to Insanity because Karen chose that in onboarding.
    """
    if chat_id is not None:
        try:
            from memory_store import get_fact
            name = (get_fact(int(chat_id), "preferred_name") or "").strip()
            if name:
                return name
        except Exception:
            pass

    return "Insanity"


def warm_open(chat_id: int | None = None, emoji: str = "😌📁") -> str:
    name = get_karen_display_name(chat_id)
    return f"Claro, {name} {emoji}"


def beta_legal_boundary() -> str:
    return (
        "Nota rápida: esto te ayuda a organizar memoria, hechos, documentos y preguntas. "
        "No reemplaza a un abogado, porque todavía no me dieron toga ni licencia, gracias a Dios. 😏"
    )


def consultative_next_step(topic: str = "abogado") -> str:
    if topic == "abogado":
        return (
            "Siguiente paso sugerido:\n"
            "Esto es lo que recomiendo revisar ahora. Pero dime algo importante: "
            "¿ya tienes una cita, llamada o plan con abogado esta semana? "
            "Si me das fecha/hora o lo que falta coordinar, lo dejamos como seguimiento o recordatorio."
        )

    return (
        "Siguiente paso sugerido:\n"
        "Dime si ya tienes un plan, fecha o responsable para esto, y lo dejamos ordenado."
    )


def saved_case_intro(chat_id: int | None = None) -> str:
    return (
        f"{warm_open(chat_id)}\n\n"
        "Esto es lo que tengo guardado del caso del terreno hasta ahora:"
    )
