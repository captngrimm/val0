# KAREN MULTIMEDIA + FORGE OCR NOTES

## Date
2026-05-10

## Status
Parking Lot / Next Architecture Thread

## Why this exists

Karen wants to eventually send:
- photos of land/case documents
- photos of plans/maps
- Word/PDF files
- scanned registry/public documents
- audio notes

Val0 should eventually log these as case attachments and, where possible, extract useful legal/admin data.

Important: Frank remembers there may already be an OCR/PDF pipeline built for Miguel Legal MVP, possibly on Forge / ValPrime, not directly inside Val0.

This file exists so we do not forget that trail.

## Current Val0 state

Current bot handler inspection shows Val0 has active handlers for:
- TEXT
- VOICE

No active PHOTO/DOCUMENT Telegram handlers were found in the inspected bot registration block.

So Val0 currently does not appear to ingest Telegram photos/documents directly.

## Important architecture distinction

Val0:
- client-facing Telegram bot
- Karen LandOps memory/case flow
- reminders
- recent events
- lawyer package
- document inventory as text

Forge / ValPrime:
- likely contains deeper operator tooling
- may include OCR/PDF pipeline used or planned for Miguel Legal MVP
- should be inspected before rebuilding OCR/document ingestion from scratch

## Desired future user flow

Karen sends a photo/document with caption:

"Foto del documento del Registro Público"

Val should respond:

"Recibí una imagen/documento y lo dejé asociado al caso del terreno 📎.
Por ahora queda como pendiente de revisar.
Si quieres, intento extraer finca, folio, tomo, fecha, nombres o notaría."

## Target v0 capability

Attachment Logging v0:
- detect Telegram photo/document
- store Telegram file_id
- store file type
- store caption
- associate with KAREN-LAND-001
- show it in recent activity / lawyer package as attachment reference
- no OCR yet

## Target v1 capability

Document/Image Review v1:
- download file
- send to Forge/ValPrime OCR pipeline if available
- extract obvious text/data
- save extracted text as case note
- ask user to confirm uncertain fields

## Target v2 capability

Legal document ingest:
- PDF/Word/photo ingestion
- OCR/text extraction
- structured extraction:
  - finca
  - folio
  - tomo/rollo
  - escritura
  - fecha
  - notaría
  - names
  - registry references
- link extracted facts to lawyer package

## Next action

Before coding multimedia in Val0:

1. Search Forge/ValPrime/Miguel notes for OCR/PDF pipeline.
2. Identify existing scripts, commands, paths, or docs.
3. Decide:
   - reuse Forge OCR pipeline
   - call it from Val0
   - copy minimal logic into Val0
   - defer OCR and only build attachment logging first

## Recommendation

Do not start with full OCR inside Val0.

Start with:
Attachment Logging v0 in Val0.

Then bridge to Forge OCR once the existing Miguel pipeline is located.

## Launchpad note

Launchpad is also part of the likely bridge.

Possible role:
- capture large command output safely
- move files/inspection results between Forge/ValPrime and ChatGPT
- support OCR/PDF pipeline inspection
- act as the handoff surface for document-processing results

Potential future flow:
1. Karen sends document/photo to Val0.
2. Val0 logs the attachment metadata and associates it with KAREN-LAND-001.
3. If OCR/review is needed, Val0 or operator exports/downloads file for Forge/Launchpad processing.
4. Launchpad captures OCR output or analysis result.
5. Val/Frank reviews result.
6. Confirmed summary/facts are written back into Karen case memory.

Important:
Do not rebuild OCR blindly inside Val0 until Forge/ValPrime/Launchpad OCR trail is inspected.
