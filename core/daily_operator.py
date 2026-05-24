from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any, Iterable


PRIORITIES = {"urgent", "high", "normal", "low"}
STATUSES = {
    "pending",
    "today",
    "done",
    "blocked",
    "needs_review",
    "ocr_needed",
    "unsupported",
    "ready",
    "unknown",
}
ITEM_LIST_FIELDS = (
    "calendar_items",
    "reminders",
    "tasks",
    "pending_actions",
    "case_priorities",
    "document_items",
    "timeline_items",
)
MAX_DISPLAY_TITLE_CHARS = 96


@dataclass(frozen=True)
class DailyOperatorItem:
    item_id: str
    item_type: str
    title: str
    description: str = ""
    due_at: str | None = None
    source_type: str = ""
    source_id: str = ""
    priority: str = "normal"
    status: str = "pending"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DailyOperatorSnapshot:
    client_id: str
    case_id: str
    snapshot_date: str
    calendar_items: tuple[DailyOperatorItem, ...] = ()
    reminders: tuple[DailyOperatorItem, ...] = ()
    tasks: tuple[DailyOperatorItem, ...] = ()
    pending_actions: tuple[DailyOperatorItem, ...] = ()
    case_priorities: tuple[DailyOperatorItem, ...] = ()
    document_items: tuple[DailyOperatorItem, ...] = ()
    timeline_items: tuple[DailyOperatorItem, ...] = ()
    suggested_next_action: str = ""
    warnings: tuple[str, ...] = ()
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


def normalize_operator_priority(value: str | None) -> str:
    raw = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "critical": "urgent",
        "critico": "urgent",
        "crítico": "urgent",
        "urgente": "urgent",
        "alta": "high",
        "medio": "normal",
        "medium": "normal",
        "normal": "normal",
        "baja": "low",
    }
    normalized = aliases.get(raw, raw)
    return normalized if normalized in PRIORITIES else "normal"


def normalize_operator_status(value: str | None) -> str:
    raw = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "open": "pending",
        "abierto": "pending",
        "pendiente": "pending",
        "hoy": "today",
        "complete": "done",
        "completed": "done",
        "hecho": "done",
        "cerrado": "done",
        "bloqueado": "blocked",
        "review": "needs_review",
        "revision": "needs_review",
        "revisión": "needs_review",
        "manual_review": "needs_review",
        "human_review": "needs_review",
        "needs_human_review": "needs_review",
        "ocr": "ocr_needed",
        "ocr_needed": "ocr_needed",
        "ocr_failed": "needs_review",
        "unsupported": "unsupported",
        "no_soportado": "unsupported",
        "no_soportada": "unsupported",
        "listo": "ready",
        "lista": "ready",
        "stored": "pending",
        "guardado": "pending",
        "registered": "pending",
        "registrado": "pending",
        "unknown": "unknown",
    }
    normalized = aliases.get(raw, raw)
    return normalized if normalized in STATUSES else "unknown"


def _today_text(snapshot_date: str | date | datetime | None) -> str:
    if isinstance(snapshot_date, datetime):
        return snapshot_date.date().isoformat()
    if isinstance(snapshot_date, date):
        return snapshot_date.isoformat()
    raw = str(snapshot_date or "").strip()
    return raw[:10] if raw else date.today().isoformat()


def _item_from_any(value: Any, fallback_type: str) -> DailyOperatorItem | None:
    if value is None:
        return None
    if isinstance(value, DailyOperatorItem):
        return DailyOperatorItem(
            item_id=value.item_id,
            item_type=value.item_type or fallback_type,
            title=value.title,
            description=value.description,
            due_at=value.due_at,
            source_type=value.source_type,
            source_id=value.source_id,
            priority=normalize_operator_priority(value.priority),
            status=normalize_operator_status(value.status),
            metadata=dict(value.metadata or {}),
        )

    if isinstance(value, dict):
        title = str(value.get("title") or value.get("summary") or value.get("text") or "").strip()
        if not title:
            return None
        item_id = str(value.get("item_id") or value.get("id") or value.get("source_id") or title).strip()
        return DailyOperatorItem(
            item_id=item_id,
            item_type=str(value.get("item_type") or fallback_type).strip() or fallback_type,
            title=title,
            description=str(value.get("description") or "").strip(),
            due_at=str(value.get("due_at") or value.get("due_at_utc") or value.get("event_date") or "").strip() or None,
            source_type=str(value.get("source_type") or value.get("source") or fallback_type).strip(),
            source_id=str(value.get("source_id") or value.get("id") or "").strip(),
            priority=normalize_operator_priority(value.get("priority")),
            status=normalize_operator_status(value.get("status")),
            metadata=dict(value.get("metadata") or {}),
        )

    title = str(value).strip()
    if not title:
        return None
    return DailyOperatorItem(
        item_id=title,
        item_type=fallback_type,
        title=title,
        source_type=fallback_type,
        source_id=title,
    )


def _items(values: Iterable[Any] | None, fallback_type: str) -> tuple[DailyOperatorItem, ...]:
    out: list[DailyOperatorItem] = []
    seen = set()
    for value in values or ():
        item = _item_from_any(value, fallback_type)
        if not item:
            continue
        key = (item.item_type, item.item_id)
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return tuple(out)


def build_daily_operator_snapshot(
    *,
    client_id: str = "",
    case_id: str = "",
    snapshot_date: str | date | datetime | None = None,
    calendar_items: Iterable[Any] | None = None,
    reminders: Iterable[Any] | None = None,
    tasks: Iterable[Any] | None = None,
    pending_actions: Iterable[Any] | None = None,
    case_priorities: Iterable[Any] | None = None,
    document_items: Iterable[Any] | None = None,
    timeline_items: Iterable[Any] | None = None,
    suggested_next_action: str = "",
    warnings: Iterable[Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> DailyOperatorSnapshot:
    snapshot = DailyOperatorSnapshot(
        client_id=str(client_id or "").strip(),
        case_id=str(case_id or "").strip(),
        snapshot_date=_today_text(snapshot_date),
        calendar_items=_items(calendar_items, "calendar"),
        reminders=_items(reminders, "reminder"),
        tasks=_items(tasks, "task"),
        pending_actions=_items(pending_actions, "pending_action"),
        case_priorities=_items(case_priorities, "case_priority"),
        document_items=_items(document_items, "document"),
        timeline_items=_items(timeline_items, "timeline"),
        suggested_next_action=str(suggested_next_action or "").strip(),
        warnings=tuple(str(w).strip() for w in (warnings or ()) if str(w or "").strip()),
        metadata=dict(metadata or {}),
    )
    if snapshot.suggested_next_action:
        return snapshot
    return DailyOperatorSnapshot(
        **{
            **snapshot.__dict__,
            "suggested_next_action": choose_suggested_next_action(snapshot),
        }
    )


def filter_today_items(items: Iterable[DailyOperatorItem], snapshot_date: str | date | datetime | None) -> list[DailyOperatorItem]:
    today = _today_text(snapshot_date)
    out = []
    for item in items or ():
        due = str(item.due_at or "").strip()
        status = normalize_operator_status(item.status)
        if due.startswith(today) or status == "today":
            out.append(item)
    return out


def _has_due_date(item: DailyOperatorItem) -> bool:
    return bool(str(item.due_at or "").strip())


def _due_date_text(item: DailyOperatorItem) -> str:
    raw = str(item.due_at or "").strip()
    if len(raw) >= 10:
        candidate = raw[:10]
        try:
            date.fromisoformat(candidate)
            return candidate
        except ValueError:
            return ""
    return ""


def _is_overdue(item: DailyOperatorItem, snapshot_date: str | date | datetime | None) -> bool:
    due = _due_date_text(item)
    today = _today_text(snapshot_date)
    return bool(due and due < today)


def _is_upcoming_or_today(item: DailyOperatorItem, snapshot_date: str | date | datetime | None) -> bool:
    due = _due_date_text(item)
    today = _today_text(snapshot_date)
    return bool(due and due >= today)


def _is_today_or_explicit_today(item: DailyOperatorItem, snapshot_date: str | date | datetime | None) -> bool:
    due = _due_date_text(item)
    today = _today_text(snapshot_date)
    return bool((due and due == today) or (not due and normalize_operator_status(item.status) == "today"))


def _is_future(item: DailyOperatorItem, snapshot_date: str | date | datetime | None) -> bool:
    due = _due_date_text(item)
    today = _today_text(snapshot_date)
    return bool(due and due > today)


def _is_done(item: DailyOperatorItem) -> bool:
    return normalize_operator_status(item.status) == "done"


def _is_generic_case_review(item: DailyOperatorItem) -> bool:
    title = _clean_string(item.title).lower()
    generic_titles = {
        "revisar próximos pasos del caso activo",
        "revisar proximos pasos del caso activo",
        "revisar próximos pasos",
        "revisar proximos pasos",
    }
    return item.item_type == "case_priority" and title in generic_titles


def _ranked_candidates(items: Iterable[DailyOperatorItem]) -> list[DailyOperatorItem]:
    priority_rank = {"urgent": 0, "high": 1, "normal": 2, "low": 3}
    status_penalty = {"blocked": 1, "done": 9}
    candidates = [item for item in items or () if not _is_done(item)]
    candidates.sort(
        key=lambda item: (
            priority_rank.get(normalize_operator_priority(item.priority), 2),
            status_penalty.get(normalize_operator_status(item.status), 0),
            str(item.due_at or "9999-99-99"),
            item.title,
        )
    )
    return candidates


def _ranked_recent_documents(items: Iterable[DailyOperatorItem]) -> list[DailyOperatorItem]:
    priority_rank = {"urgent": 0, "high": 1, "normal": 2, "low": 3}
    candidates = [item for item in items or () if not _is_done(item)]
    candidates.sort(key=lambda item: item.title)
    candidates.sort(key=lambda item: str(item.due_at or ""), reverse=True)
    candidates.sort(key=lambda item: priority_rank.get(normalize_operator_priority(item.priority), 2))
    return candidates


def choose_suggested_next_action(snapshot: DailyOperatorSnapshot) -> str:
    today_action_candidates = []
    future_action_candidates = []
    overdue_action_candidates = []
    for field in ("calendar_items", "reminders", "tasks"):
        field_items = list(getattr(snapshot, field))
        today_action_candidates.extend(
            item for item in field_items
            if _is_today_or_explicit_today(item, snapshot.snapshot_date)
        )
        future_action_candidates.extend(
            item for item in field_items
            if _is_future(item, snapshot.snapshot_date)
        )
        overdue_action_candidates.extend(
            item for item in field_items
            if _is_overdue(item, snapshot.snapshot_date)
        )

    concrete_case_priorities = [
        item for item in snapshot.case_priorities
        if not _is_generic_case_review(item)
    ]
    generic_case_priorities = [
        item for item in snapshot.case_priorities
        if _is_generic_case_review(item)
    ]
    ranked_groups = (
        (today_action_candidates, _ranked_candidates),
        (future_action_candidates, _ranked_candidates),
        (list(snapshot.pending_actions), _ranked_candidates),
        (concrete_case_priorities, _ranked_candidates),
        (list(snapshot.document_items), _ranked_recent_documents),
        (list(snapshot.timeline_items), _ranked_candidates),
        (overdue_action_candidates, _ranked_candidates),
        (generic_case_priorities, _ranked_candidates),
    )

    for group, ranker in ranked_groups:
        candidates = ranker(group)
        if not candidates:
            continue
        return _next_action_label(candidates[0], snapshot_date=snapshot.snapshot_date)
    return "Elegir una prioridad concreta para hoy"


def _safe_item(item: DailyOperatorItem, *, snapshot_date: str | date | datetime | None = None) -> dict[str, Any]:
    return {
        "item_id": item.item_id,
        "item_type": item.item_type,
        "title": _clean_display_title(item.title, fallback="(sin título)"),
        "description": _truncate_text(item.description, 140),
        "due_at": item.due_at,
        "source_type": item.source_type,
        "source_id": item.source_id,
        "priority": normalize_operator_priority(item.priority),
        "status": _status_display_label(item, snapshot_date=snapshot_date),
        "raw_status": normalize_operator_status(item.status),
    }


def safe_daily_operator_summary(snapshot: DailyOperatorSnapshot) -> dict[str, Any]:
    return {
        "client_id": snapshot.client_id,
        "case_id": snapshot.case_id,
        "snapshot_date": snapshot.snapshot_date,
        "calendar_items": [_safe_item(item, snapshot_date=snapshot.snapshot_date) for item in snapshot.calendar_items],
        "reminders": [_safe_item(item, snapshot_date=snapshot.snapshot_date) for item in snapshot.reminders],
        "tasks": [_safe_item(item, snapshot_date=snapshot.snapshot_date) for item in snapshot.tasks],
        "pending_actions": [_safe_item(item, snapshot_date=snapshot.snapshot_date) for item in snapshot.pending_actions],
        "case_priorities": [_safe_item(item, snapshot_date=snapshot.snapshot_date) for item in snapshot.case_priorities],
        "document_items": [_safe_item(item, snapshot_date=snapshot.snapshot_date) for item in snapshot.document_items],
        "timeline_items": [_safe_item(item, snapshot_date=snapshot.snapshot_date) for item in snapshot.timeline_items],
        "suggested_next_action": snapshot.suggested_next_action,
        "warnings": list(snapshot.warnings),
        "created_at": snapshot.created_at,
    }


def _get_value(row: Any, *keys: str, default: Any = "") -> Any:
    for key in keys:
        if isinstance(row, dict) and key in row:
            return row.get(key)
        if hasattr(row, key):
            return getattr(row, key)
    return default


def _clean_string(value: Any) -> str:
    return " ".join(str(value or "").replace("\n", " ").split()).strip()


def _truncate_text(value: Any, limit: int = MAX_DISPLAY_TITLE_CHARS) -> str:
    text = _clean_string(value)
    if len(text) <= limit:
        return text
    trimmed = text[: max(0, limit - 1)].rstrip(" .,;:-")
    return f"{trimmed}…"


def _clean_display_title(value: Any, *, fallback: str = "", limit: int = MAX_DISPLAY_TITLE_CHARS) -> str:
    text = _clean_string(value)
    for prefix in (
        "recordatorio:",
        "recordatorio",
        "tarea:",
        "tarea",
        "nota:",
        "nota",
        "case note:",
        "case_note:",
    ):
        if text.lower().startswith(prefix):
            text = text[len(prefix):].strip(" :-")
            break
    return _truncate_text(text or fallback, limit)


def _status_display_label(item: DailyOperatorItem, *, snapshot_date: str | date | datetime | None = None) -> str:
    status = normalize_operator_status(item.status)
    if snapshot_date is not None and item.item_type in {"calendar", "reminder", "task"} and _is_overdue(item, snapshot_date):
        return "vencido por revisar"
    if status in {"pending", "today", "ready"}:
        return ""
    if status == "unknown":
        return "estado por revisar" if item.item_type == "document" else ""
    labels = {
        "done": "hecho",
        "blocked": "bloqueado",
        "needs_review": "requiere revisión",
        "ocr_needed": "requiere OCR/revisión",
        "unsupported": "no extraíble automático",
    }
    return labels.get(status, "")


def _next_action_label(item: DailyOperatorItem, *, snapshot_date: str | date | datetime | None = None) -> str:
    title = _clean_display_title(item.title)
    if item.item_type == "pending_action":
        return f"Responder la confirmación pendiente: {title}"
    if item.item_type in {"calendar", "reminder", "task"}:
        if snapshot_date is not None and _is_overdue(item, snapshot_date):
            return f"Pendiente vencido por revisar: {title}"
        if snapshot_date is not None and _is_upcoming_or_today(item, snapshot_date):
            due = _due_date_text(item)
            if due and due > _today_text(snapshot_date):
                return f"Próximo pendiente: {title}"
        return f"Atender hoy: {title}"
    if item.item_type == "case_priority":
        return title if title.lower().startswith("revisar") else f"Revisar: {title}"
    if item.item_type == "document":
        status = normalize_operator_status(item.status)
        if status in {"ocr_needed", "needs_review", "unknown"}:
            return f"Revisar documento pendiente: {title}"
        if status == "unsupported":
            return f"Decidir revisión manual para: {title}"
        return f"Revisar documento: {title}"
    if item.item_type == "timeline":
        return f"Revisar cronología: {title}"
    return title or "Elegir una prioridad concreta para hoy"


def _safe_metadata(row: Any, allowed_keys: Iterable[str]) -> dict[str, Any]:
    out = {}
    for key in allowed_keys:
        value = _get_value(row, key, default=None)
        if value is None:
            continue
        out[key] = value
    return out


def collect_calendar_items(events: Iterable[Any] | None, *, source_type: str = "google_calendar") -> tuple[DailyOperatorItem, ...]:
    items = []
    for event in events or ():
        title = _clean_display_title(_get_value(event, "title", "summary", "text", default=""))
        if not title:
            title = "(sin título)"
        event_id = _clean_string(_get_value(event, "item_id", "id", "event_id", "source_id", default=title))
        due_at = _clean_string(_get_value(event, "due_at", "start", "start_iso", "dateTime", default="")) or None
        items.append(
            DailyOperatorItem(
                item_id=event_id,
                item_type="calendar",
                title=title,
                description=_clean_string(_get_value(event, "description", default="")),
                due_at=due_at,
                source_type=_clean_string(_get_value(event, "source_type", "source", default=source_type)) or source_type,
                source_id=_clean_string(_get_value(event, "source_id", "id", "event_id", default=event_id)),
                priority=normalize_operator_priority(_get_value(event, "priority", default="normal")),
                status=normalize_operator_status(_get_value(event, "status", default="pending")),
                metadata=_safe_metadata(event, ("calendar_id", "html_link")),
            )
        )
    return _items(items, "calendar")


def collect_reminder_items(reminders: Iterable[Any] | None) -> tuple[DailyOperatorItem, ...]:
    items = []
    for reminder in reminders or ():
        title = _clean_display_title(_get_value(reminder, "title", "text", "summary", default=""))
        if not title:
            continue
        reminder_id = _clean_string(_get_value(reminder, "item_id", "id", "source_id", default=title))
        items.append(
            DailyOperatorItem(
                item_id=reminder_id,
                item_type="reminder",
                title=title,
                description=_clean_string(_get_value(reminder, "description", default="")),
                due_at=_clean_string(_get_value(reminder, "due_at", "due_at_utc", "due_date", default="")) or None,
                source_type=_clean_string(_get_value(reminder, "source_type", "source", default="reminder")) or "reminder",
                source_id=_clean_string(_get_value(reminder, "source_id", "id", default=reminder_id)),
                priority=normalize_operator_priority(_get_value(reminder, "priority", default="normal")),
                status=normalize_operator_status(_get_value(reminder, "status", default="pending")),
                metadata=_safe_metadata(reminder, ("entity_type", "parent_ref", "channel")),
            )
        )
    return _items(items, "reminder")


def collect_task_items(tasks: Iterable[Any] | None) -> tuple[DailyOperatorItem, ...]:
    items = []
    for task in tasks or ():
        title = _clean_display_title(_get_value(task, "title", "action", "task_text", "text", "summary", "raw_input", default=""))
        if not title:
            action = _clean_string(_get_value(task, "action", default=""))
            target = _clean_string(_get_value(task, "target", default=""))
            title = _clean_display_title(" ".join(x for x in (action, target) if x).strip())
        if not title:
            continue
        task_id = _clean_string(_get_value(task, "item_id", "id", "source_id", default=title))
        items.append(
            DailyOperatorItem(
                item_id=task_id,
                item_type="task",
                title=title,
                description=_clean_string(_get_value(task, "description", default="")),
                due_at=_clean_string(_get_value(task, "due_at", "due_date", default="")) or None,
                source_type=_clean_string(_get_value(task, "source_type", "source", default="commitment")) or "commitment",
                source_id=_clean_string(_get_value(task, "source_id", "id", default=task_id)),
                priority=normalize_operator_priority(_get_value(task, "priority", default="normal")),
                status=normalize_operator_status(_get_value(task, "status", default="pending")),
                metadata=_safe_metadata(task, ("confidence",)),
            )
        )
    return _items(items, "task")


def collect_pending_action_items(actions: Iterable[Any] | None) -> tuple[DailyOperatorItem, ...]:
    items = []
    for action in actions or ():
        title = _clean_display_title(_get_value(action, "title", "display_summary", "summary", "action_type", default=""))
        if not title:
            continue
        action_id = _clean_string(_get_value(action, "item_id", "action_id", "id", "source_id", default=title))
        items.append(
            DailyOperatorItem(
                item_id=action_id,
                item_type="pending_action",
                title=title,
                description=_clean_string(_get_value(action, "description", "action_type", default="")),
                due_at=_clean_string(_get_value(action, "expires_at", "due_at", default="")) or None,
                source_type=_clean_string(_get_value(action, "source_type", "source", default="pending_action")) or "pending_action",
                source_id=_clean_string(_get_value(action, "source_id", "action_id", "id", default=action_id)),
                priority="high",
                status=normalize_operator_status(_get_value(action, "status", default="pending")),
                metadata=_safe_metadata(action, ("action_type", "created_by")),
            )
        )
    return _items(items, "pending_action")


def collect_case_priority_items(items: Iterable[Any] | None) -> tuple[DailyOperatorItem, ...]:
    out = []
    for item in items or ():
        title = _clean_display_title(_get_value(item, "title", "summary", "note_text", "text", default=""))
        if not title:
            continue
        item_id = _clean_string(_get_value(item, "item_id", "id", "source_id", default=title))
        out.append(
            DailyOperatorItem(
                item_id=item_id,
                item_type="case_priority",
                title=title,
                description=_clean_string(_get_value(item, "description", default="")),
                due_at=_clean_string(_get_value(item, "due_at", "event_date", "created_at", default="")) or None,
                source_type=_clean_string(_get_value(item, "source_type", "source", default="case_priority")) or "case_priority",
                source_id=_clean_string(_get_value(item, "source_id", "id", default=item_id)),
                priority=normalize_operator_priority(_get_value(item, "priority", default="high")),
                status=normalize_operator_status(_get_value(item, "status", default="pending")),
                metadata=_safe_metadata(item, ("case_id", "tag")),
            )
        )
    return _items(out, "case_priority")


def _document_status_from_record(record: Any) -> str:
    raw = _clean_string(_get_value(record, "status", "state", default="")).lower()
    if "unsupported" in raw or "no soport" in raw:
        return "unsupported"
    if "ocr" in raw or "manual" in raw or "revisión" in raw or "revision" in raw:
        return "ocr_needed"
    return normalize_operator_status(raw)


def collect_document_review_items(records: Iterable[Any] | None) -> tuple[DailyOperatorItem, ...]:
    review_statuses = {"pending", "needs_review", "ocr_needed", "unsupported", "unknown"}
    items = []
    for record in records or ():
        status = _document_status_from_record(record)
        if status not in review_statuses:
            continue
        filename = _clean_display_title(_get_value(record, "filename", "title", "name", default="documento"), fallback="documento")
        caption = _truncate_text(_get_value(record, "caption", "description", default=""), 140)
        document_id = _clean_string(_get_value(record, "document_id", "item_id", "id", "source_id", default=filename))
        items.append(
            DailyOperatorItem(
                item_id=document_id,
                item_type="document",
                title=filename,
                description=caption,
                due_at=_clean_string(_get_value(record, "created_at", default="")) or None,
                source_type=_clean_string(_get_value(record, "source_type", "source", default="document")) or "document",
                source_id=_clean_string(_get_value(record, "source_id", "document_id", "ingest_id", "id", default=document_id)),
                priority="normal" if status == "pending" else "high",
                status=status,
                metadata=_safe_metadata(record, ("mime_type", "ingest_id", "source_message_id")),
            )
        )
    return _items(items, "document")


def collect_timeline_items(events: Iterable[Any] | None) -> tuple[DailyOperatorItem, ...]:
    items = []
    for event in events or ():
        title = _clean_display_title(_get_value(event, "title", "summary", "description", default=""))
        if not title:
            continue
        event_id = _clean_string(_get_value(event, "event_id", "item_id", "id", "source_id", default=title))
        items.append(
            DailyOperatorItem(
                item_id=event_id,
                item_type="timeline",
                title=title,
                description=_clean_string(_get_value(event, "description", default="")),
                due_at=_clean_string(_get_value(event, "event_date", "due_at", "created_at", default="")) or None,
                source_type=_clean_string(_get_value(event, "source_type", "source", default="case_timeline")) or "case_timeline",
                source_id=_clean_string(_get_value(event, "source_id", "id", default=event_id)),
                priority=normalize_operator_priority(_get_value(event, "priority", default="normal")),
                status=normalize_operator_status(_get_value(event, "status", default="ready")),
                metadata=_safe_metadata(event, ("confidence", "document_id", "ingest_id")),
            )
        )
    return _items(items, "timeline")


def build_daily_operator_snapshot_from_sources(
    *,
    client_id: str = "",
    case_id: str = "",
    snapshot_date: str | date | datetime | None = None,
    calendar_events: Iterable[Any] | None = None,
    reminders: Iterable[Any] | None = None,
    tasks: Iterable[Any] | None = None,
    pending_actions: Iterable[Any] | None = None,
    case_priority_sources: Iterable[Any] | None = None,
    document_records: Iterable[Any] | None = None,
    timeline_events: Iterable[Any] | None = None,
    warnings: Iterable[Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> DailyOperatorSnapshot:
    return build_daily_operator_snapshot(
        client_id=client_id,
        case_id=case_id,
        snapshot_date=snapshot_date,
        calendar_items=collect_calendar_items(calendar_events),
        reminders=collect_reminder_items(reminders),
        tasks=collect_task_items(tasks),
        pending_actions=collect_pending_action_items(pending_actions),
        case_priorities=collect_case_priority_items(case_priority_sources),
        document_items=collect_document_review_items(document_records),
        timeline_items=collect_timeline_items(timeline_events),
        warnings=warnings,
        metadata=metadata,
    )
