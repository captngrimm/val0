=====================================================================
SPRINT 13 — CASE STATUS / RESUMEN DEL CASO
=====================================================================

Objective
---------
Allow users to ask naturally for the current state of a case without
memorizing rigid command syntax.

Supported natural phrases
-------------------------
- resumen del caso <id>
- dame un resumen del caso <id>
- estado del caso <id>
- cómo va el caso <id>
- por donde va el caso <id>
- situación actual del caso <id>

Behavior
--------
All supported phrasings route to the same deterministic case-status
function.

The function returns:

- latest valid note
- next pending reminder
- quick counts

Implementation
--------------
File:
- core/case_mvp.py
- bot.py

Added:
- try_case_status(...)

Routing:
- bot.py imports try_case_status
- status gate runs before timeline/detail gates

Important fixes
---------------
1. Expanded regex to support natural Spanish phrasing.
2. Prevented status-like user queries from being captured as case notes.
3. Filtered polluted historical note rows from "última nota" summary display.

Result
------
Users can now ask naturally about case status while still receiving a
deterministic answer grounded in stored case data.

Example
-------
Input:
cómo va el caso 524242024

Output:
🗂️ CASE:524242024

Resumen del caso
- última nota: juez sugirió conciliación otra vez
- próximo pendiente: —

Conteo rápido
- notas: 18
- recordatorios pendientes: 0

Architectural impact
--------------------
This is the first deterministic natural-language intent layer for legal
workflow retrieval.

Natural user phrasing
→ intent detection
→ deterministic retrieval
→ grounded response

This preserves conversational usability without handing truth control to
the LLM.

