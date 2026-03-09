=====================================================================
SPRINT 14 — CLIENT NAME → CASE RESOLUTION
=====================================================================

Objective
---------
Allow users to reference a case by client name instead of expediente.

Examples
--------
registrar caso 524242024 cliente Leticia

cómo va el caso de Leticia
estado del caso de Leticia
resumen del caso de Leticia
situación actual del caso de Leticia

Behavior
--------
1. User registers a client name to an expediente.
2. System stores that mapping in cases table.
3. Natural-language case status queries using the client name are resolved
   to the expediente.
4. Existing deterministic case-status engine is reused.

Schema
------
Table: cases

Relevant columns:
- expediente
- client_name
- client_alias
- chat_id

Implementation
--------------
Files:
- memory_store.py
- bot.py
- core/case_mvp.py

Added DB helpers:
- upsert_case(...)
- get_case_by_client_name(...)

Added deterministic registration command:
- registrar caso <expediente> cliente <nombre>

Added name-based resolution in try_case_status(...):
- direct expediente query path
- client-name query path

Important fixes
---------------
1. Added missing client_alias column in the encrypted DB.
2. Prevented registration commands from being captured as case notes.
3. Filtered polluted historical registration rows from latest-note summary.

Result
------
Users can now ask for case status by client name, not only by expediente.

Example
-------
Input:
cómo va el caso de Leticia

Output:
🗂️ CASE:524242024

Resumen del caso
- última nota: juez sugirió conciliación otra vez
- próximo pendiente: —

Conteo rápido
- notas: 19
- recordatorios pendientes: 0

Architectural impact
--------------------
This introduces the first human-friendly entity alias layer.

client name
→ case resolver
→ deterministic case engine

This is a major UX improvement because users no longer need to memorize
expediente numbers.

