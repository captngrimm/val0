# Query Playbook — Timeline Split (v4)

Status: APPROVED (Manual)
Scope: VFMS / Legal / Deterministic Outputs
Last validated: 2025-12-26




# LEGAL_NOAH — TIMELINE GENERATION (v4)
# Deterministic. Grounded. No inference.

## PURPOSE
Generate a chronological timeline from FACTS_DATES outputs, split into:
1) Case Events Timeline
2) Legal References Timeline

This prevents statute citations from polluting the factual case history.

---

## INPUT
- Source directory: vfms_data/outputs/legal_noah_docs/*.md
- Each file must be generated with:
  - "Extrae SOLO fechas… No infieras."

---

## CLASSIFICATION RULES (DETERMINISTIC)

### A) CASE EVENT
A date entry is classified as a **CASE EVENT** if:
- The literal text contains any of:
  - AUTO
  - PROVIDENCIA
  - SENTENCIA
  - ACTA
  - AUDIENCIA
  - INCIDENTE
  - RESUELVE
  - ADMITE
  - ORDENA
  - NIEGA
  - TRASLADO
- AND references at least one:
  - party (Franklin, Catherine, Noah)
  - court action
  - expediente number
  - procedural step

### B) LEGAL REFERENCE
A date entry is classified as a **LEGAL REFERENCE** if:
- The literal text contains:
  - Ley
  - Código
  - Artículo
  - Constitución
  - Reglas
- AND does NOT describe a procedural action in the case

### C) UNKNOWN / AMBIGUOUS
If neither condition is met:
- Place entry under **REVIEW_REQUIRED**
- Do not discard
- Do not guess

---

## OUTPUT FORMAT

### 1️⃣ CASE TIMELINE
Sorted chronologically.
Each entry includes:
- date (ISO normalized if possible)
- doc filename
- ingest_id
- literal text (verbatim excerpt)

### 2️⃣ LEGAL REFERENCES
Sorted chronologically.
Same metadata as above.
Clearly labeled as *contextual law*, not case events.

### 3️⃣ REVIEW_REQUIRED
Explicitly surfaced for human review.

---

## GUARANTEES
- No inference
- No rewording
- No sentiment
- No pattern speculation
- Same input → same output

---

## FAILURE MODE
If no FACTS files are found:
- Abort with error
- Do not generate empty timelines
