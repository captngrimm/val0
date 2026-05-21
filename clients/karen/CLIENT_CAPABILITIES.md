# CLIENT_CAPABILITIES — Karen / Val Personal

Purpose:
Track capabilities active, testing, planned, and deferred for Karen.

---

## Active / sealed

### client_context_reader_v0
Status: active
What Karen can ask:
- Val, ¿qué puedes hacer hoy?
- Val, ¿qué viene después?
- Val, ¿estamos a tiempo?

### client_ideas_v0
Status: active
What Karen can ask:
- Val, tengo una idea: ...
- Val, ¿qué ideas tengo guardadas?

### grocery_list_v0
Status: active
What Karen can do:
- add grocery items
- list grocery items
- delete grocery items

Examples:
- Val, anota huevos, pan y café para el súper.
- Val, ¿qué tengo en la lista del súper?
- Val, borra pan de la lista del súper.
- quitar café

### karen_legal_case_v0
Status: active
What it supports:
- land/finca/family legal-admin case context
- case facts
- case status
- case-related summaries

### carpeta_clara_v0
Status: active
What it supports:
- organizing scattered documents
- starting document inventory
- preparing document flow for lawyer/admin review

### nora_lawyer_package_v0
Status: active
What it supports:
- Nora lawyer prep package
- missing checklist
- lawyer questions

---

## Testing / needs more QA

### reminders_agenda_v0
Status: testing
Notes:
- basic reminders and agenda routes exist
- needs more real Karen testing

### voice_capture_v0
Status: testing
Notes:
- voice pipeline works sometimes
- observed failures downloading/transcribing voice messages

---

## Planned next

### grocery_metadata_v0
Status: planned
Goal:
Manual product metadata:
- price
- store
- aisle/location
- date

Example:
Val, anota leche Dos Pinos a $2.49 en Riba Smith, pasillo lácteos.

---

## Deferred / later

### photo_ocr_product_v0
Status: deferred
Includes:
- product photo
- barcode
- nutrition facts
- receipt OCR

Reason:
Needs stable image/OCR pipeline and should come after manual metadata.
