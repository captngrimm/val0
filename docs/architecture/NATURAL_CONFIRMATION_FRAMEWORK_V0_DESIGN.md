# Natural Confirmation Framework v0 Design

## Purpose

Val0 has several high-trust flows where a short user reply like `sí`, `dale`, `ok`, or `cancelar` can create, delete, register, or continue an action. Today those flows are implemented separately. Natural Confirmation Framework v0 defines a reusable confirmation engine so calendar create/delete, reminders, grocery deletion, document actions, and future tool actions can share one safe pattern without giving the LLM or router execution authority.

The framework should centralize pending action state, confirmation parsing, expiration, audit metadata, and deterministic execution boundaries.

## Current Confirmation Flow Map

| Flow | Current State | Confirmation Path | Executor | Current Risk |
| --- | --- | --- | --- | --- |
| Google Calendar create | `_PENDING_GCAL_APPOINTMENT_DRAFTS` in `bot.py` | `maybe_handle_pending_gcal_appointment_confirmation` | `create_client_event` | Safe explicit confirmation exists, but state shape is custom. |
| Google Calendar delete | `_PENDING_GCAL_DELETE_DRAFTS` in `bot.py` | `maybe_handle_pending_gcal_delete_confirmation` | `delete_client_event` | Safe explicit confirmation exists, but state shape is custom. |
| Reminder / case event confirmation | `_PENDING_REMINDER_CONFIRM` in `core/operator_reminders.py` | `handle_pending_reminder_confirmation` | `insert_case_event` | Similar to term confirmation but separate normalization and words. |
| Term confirmation | `_PENDING_TERM_CONFIRM` in `bot.py` | inline pending term block | `insert_case_event` | Similar duplicate guard and confirmation parsing repeated inline. |
| Case disambiguation | `_PENDING_CASE_DISAMBIG` in `bot.py` | inline choice handler | may create pending term/reminder or insert note | Selection/choice state can be confused with yes/no confirmation. |
| Pending next action | `context.user_data["karen_pending_next_action"]` | `maybe_handle_pending_next_action` and `is_confirmation` | deterministic Karen flow action | Uses its own confirmation vocabulary and state shape. |
| Document inventory callback confirmation | Telegram callback data, e.g. `karen:start_document_inventory` | `karen_next_action_callback` | `start_document_inventory` | Button confirmation is safer but separate from text confirmation. |
| Bug/feedback/idea pending report | `_PENDING_BUG_REPORT` | `handle_pending_bug_report` | report storage | Separate report state, should remain isolated but can share expiration/audit concepts. |
| Grocery delete/add direct mutation | client grocery file | `render_client_context_answer` / `render_client_grocery_delete` | grocery file mutation | Delete/add can mutate without a reusable explicit confirmation layer. |
| Reminder action intercept | no pending confirmation | `handle_reminder_action_intercept` | `apply_reminder_action` | Direct deterministic action; may need confirmation for destructive variants later. |
| Technical paste guard | no pending action | `looks_like_technical_paste` | safe reply only | Must run before confirmations; technical paste cannot confirm actions. |

## Duplicate Patterns And Risks

- Repeated yes/no word sets across calendar, reminders, terms, shortcuts, and next-action flows.
- Duplicated normalization for accents, punctuation, Val-prefix stripping, and whitespace.
- Inconsistent pending state shapes across dictionaries and `context.user_data`.
- Mostly missing expiration for pending actions.
- Stale confirmations can be triggered later if state survives longer than intended.
- Wrong pending flow can steal `sí`, `ok`, or `dale` when ordering changes.
- Inconsistent audit behavior: Google Calendar has a dedicated audit JSONL path, while terms/reminders/action gates use different audit paths.
- Some logs include pending payload details that may be sensitive.
- Grocery deletion currently lacks explicit confirmation even though it mutates client state.
- Confirmation handlers often mix parsing, execution, duplicate checks, auditing, and reply rendering.

## Proposed API

### PendingAction Model

```python
@dataclass
class PendingAction:
    action_id: str
    chat_id: int
    client_id: str
    action_type: str
    display_summary: str
    confirm_words: tuple[str, ...]
    cancel_words: tuple[str, ...]
    expires_at: datetime
    payload: dict
    audit_metadata: dict
    created_at: datetime
    created_by: str = "val0"
    sensitive_payload_keys: tuple[str, ...] = ()
```

Field intent:

- `action_id`: unique id for this pending action.
- `chat_id`: Telegram chat that owns the confirmation.
- `client_id`: client identity boundary.
- `action_type`: deterministic executor key.
- `display_summary`: safe user-facing summary shown before confirmation.
- `confirm_words`: accepted confirmation vocabulary for this action.
- `cancel_words`: accepted cancellation vocabulary for this action.
- `expires_at`: hard expiration.
- `payload`: executor payload; not logged raw by default.
- `audit_metadata`: safe metadata for tracing.
- `sensitive_payload_keys`: payload fields excluded from safe logging.

### Functions

```python
def create_pending_action(action: PendingAction) -> PendingAction:
    ...

def get_pending_action(chat_id: int, action_type: str | None = None) -> PendingAction | None:
    ...

def classify_confirmation_reply(text: str, action: PendingAction) -> Literal["confirm", "cancel", "unknown"]:
    ...

def clear_pending_action(action_id: str) -> None:
    ...

def expire_pending_actions(now: datetime | None = None) -> int:
    ...

def safe_audit_payload(action: PendingAction) -> dict:
    ...

def render_confirmation_prompt(action: PendingAction) -> str:
    ...
```

Implementation notes:

- v0 can be in-memory to match current behavior.
- v1 can persist pending actions if needed.
- The framework should normalize confirmation text once.
- It should not import `bot.py`.
- It should not execute actions directly unless called by a deterministic handler/executor layer.

## Deterministic Executor Registry

The executor registry maps action type to deterministic executor function:

```python
EXECUTORS = {
    "gcal_create_event": execute_gcal_create_event,
    "gcal_delete_event": execute_gcal_delete_event,
    "case_reminder_register": execute_case_reminder_register,
    "case_term_register": execute_case_term_register,
    "grocery_delete_items": execute_grocery_delete_items,
    "document_inventory_start": execute_document_inventory_start,
}
```

Rules:

- `action_type -> executor function`.
- Router/LLM may propose but never execute.
- Deterministic handler owns execution.
- Executor re-checks `chat_id`, `client_id`, action type, and expiration.
- Executor returns a structured result; caller renders the reply.

## Safety Policy

- Destructive/create/delete actions require confirmation.
- Action must bind `chat_id` and `client_id`.
- Pending actions expire.
- No cross-client confirmation.
- No raw sensitive payload in logs.
- Technical paste cannot confirm actions.
- If more than one pending action exists for a chat, ask the user to choose instead of guessing.
- Confirmation words are scoped to an active pending action; `sí` is never global.
- LLM/conversation router may propose a pending action but cannot create external side effects.
- Deterministic executor owns all writes, deletes, tool calls, and client file mutations.
- Audit metadata should include action id, action type, client id, chat id, status, and safe summary.

## Migration Plan

### Commit 1: Framework Skeleton, No Wiring

Add `core/pending_actions.py` with:

- `PendingAction`
- confirmation text normalization
- in-memory store
- create/get/clear/expire helpers
- `classify_confirmation_reply`
- `safe_audit_payload`
- `render_confirmation_prompt`
- smoke tests

No runtime behavior change.

### Commit 2: Migrate Calendar Create/Delete

Move Google Calendar create/delete pending state from custom dictionaries to `PendingAction`.

Constraints:

- Preserve current user-facing behavior.
- Keep `create_client_event` and `delete_client_event` as deterministic executors.
- Preserve duplicate guard for calendar create.
- Preserve existing Google Calendar audit JSONL behavior.
- Do not touch OAuth, token paths, or real calendar data.

### Commit 3: Migrate One Safe Extra Flow

Recommended candidate:

- case reminder confirmation, because it already has explicit yes/no and a deterministic executor path.

Alternative candidate:

- term confirmation, because it mirrors reminder confirmation.

Later candidate:

- grocery delete confirmation, because adding confirmation is a behavior change and should be handled intentionally after framework behavior is proven.

## Required Smoke Tests

- Calendar create pending action: draft, `sí` creates once, `cancelar` creates nothing.
- Calendar create duplicate guard still prevents duplicate event creation.
- Calendar delete pending action: draft, `sí` deletes only selected event id, `cancelar` deletes nothing.
- Reminder pending action: `si/dale/registralo` registers; `no/cancelar` cancels.
- Term pending action: confirm registers; cancel clears.
- Expired pending action: `sí` does not execute.
- Wrong chat id: cannot confirm another chat’s action.
- Wrong client id: cannot confirm another client’s action.
- Multiple pending actions: ambiguous confirmation does not guess.
- Technical paste while pending: returns technical paste response and does not confirm.
- Safe audit payload excludes sensitive fields.
- Regression: compile, client isolation audit, conversation router smoke, current calendar create/delete smoke.

## Do Not Do

- Do not let LLM or router execute pending actions.
- Do not migrate all confirmation flows in one commit.
- Do not change Google Calendar create/delete behavior while introducing the framework.
- Do not remove existing duplicate guards.
- Do not log full legal/calendar/reminder payloads by default.
- Do not allow stale pending actions to live indefinitely.
- Do not allow cross-client confirmation.
- Do not make `sí` global; it must apply only to a known active pending action.
- Do not move technical paste guard after pending execution.
- Do not touch OAuth, tokens, systemd, `/etc/val0`, real client data, or memory databases for this framework.
