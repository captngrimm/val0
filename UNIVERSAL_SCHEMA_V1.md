# UNIVERSAL SCHEMA V1 — VAL CORE

Goal:
One adaptable structure for all user domains.

---

## Core Table: entries

Fields:

id (uuid)
user_id
domain (legal | personal | business | hr | warranty | custom)
type (event | task | document | purchase | note | attendance)
title
description
status (active | completed | delegated | archived)
priority (low | medium | high | critical)
due_at_utc (nullable)
metadata_json (structured flexible data)
source (manual | gcal | ocr | system)
created_at
updated_at

---

## Example Use Cases

Legal Deadline:
domain=legal
type=event
metadata_json:
{
  "case_id": "CASE:524242024",
  "court": "CSJ",
  "binding": true
}

Warranty:
domain=warranty
type=purchase
metadata_json:
{
  "price": 129.99,
  "store": "Amazon",
  "warranty_months": 6,
  "receipt_file": "file_id_xyz"
}

Attendance:
domain=hr
type=attendance
metadata_json:
{
  "employee": "Carlos",
  "check_in": "08:12",
  "check_out": "17:03",
  "late": true
}

---

Principle:
Database stores structure.
LLM interprets structure.
Deterministic rules protect critical domains (legal).

