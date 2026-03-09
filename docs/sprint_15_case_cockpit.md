=====================================================================
SPRINT 15 — CASE COCKPIT
=====================================================================

Objective
---------
Turn deterministic case status into a compact operational dashboard.

Features
--------
The case cockpit now shows:

- CASE id
- client name
- latest valid note
- next pending reminder
- recent activity
- quick counts

Example
-------
Input:
cómo va el caso de Leticia

Output:
🗂️ CASE:524242024

Cliente
- Leticia

Resumen del caso
- última nota: juez sugirió conciliación otra vez
- próximo pendiente: —

Actividad reciente
- 14:57 | juez sugirió conciliación otra vez
- 00:31 | juez sugirió conciliación otra vez
- 00:17 | nota caso 524242024: juez sugirió conciliación

Conteo rápido
- notas: 20
- recordatorios pendientes: 0

Implementation
--------------
File:
- core/case_mvp.py

Changes:
- client_name displayed in try_case_status(...)
- latest valid note shown
- next pending reminder shown
- recent activity block added using last 3 valid notes
- existing deterministic case status routing reused

Architectural impact
--------------------
This converts case status from a plain query response into a deterministic
operator dashboard inside chat.

case resolver
→ deterministic case engine
→ cockpit summary

Notes
-----
Historical polluted rows still exist in old note data and may appear in
recent activity / counts until hygiene filtering is expanded.

