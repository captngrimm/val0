#!/usr/bin/env python3
"""
create_client_template.py

Creates a new Val0 client folder with standard CLIENT_* files.

Usage:
  python3 tools/create_client_template.py angel "Ángel" corporate
  python3 tools/create_client_template.py roy "Roy" business
  python3 tools/create_client_template.py sol "Sol Adriana Duarte" business
"""

from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLIENTS_DIR = ROOT / "clients"


def slugify_client_id(value: str) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9_-]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    if not value:
        raise ValueError("client_id cannot be empty")
    return value


def write_new(path: Path, content: str) -> None:
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite existing file: {path}")
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def main() -> int:
    if len(sys.argv) < 3:
        print('Usage: python3 tools/create_client_template.py <client_id> "<display_name>" [client_type]')
        return 2

    client_id = slugify_client_id(sys.argv[1])
    display_name = sys.argv[2].strip()
    client_type = sys.argv[3].strip() if len(sys.argv) >= 4 else "personal"
    today = date.today().isoformat()

    client_dir = CLIENTS_DIR / client_id
    if client_dir.exists():
        raise FileExistsError(f"Client already exists: {client_dir}")

    client_dir.mkdir(parents=True, exist_ok=False)

    write_new(client_dir / "CLIENT_PROFILE.md", f"""
# CLIENT_PROFILE — {display_name}

Client ID:
{client_id}

Display name:
{display_name}

Client type:
{client_type}

Language:
Spanish-first unless otherwise specified.

Created:
{today}

## Notes

- This is a founder-beta client profile.
- Do not assume needs; capture them through intake.
- Keep internal fields English / language-neutral.
- Keep user-facing flows localized.
""")

    write_new(client_dir / "CLIENT_STATUS.md", f"""
# CLIENT_STATUS — {display_name}

Last updated: {today}

## Current phase

Founder-beta intake / setup.

## Working now

- Client folder created.
- Base CLIENT_* files created.
- Awaiting intake: main use case, pain points, preferred workflows, and first useful capability.

## Known limits

- No client-specific routes activated yet.
- No private facts should be assumed.
- Needs capability selection before demo.

## Next recommended build block

Run client intake:
- What do you want Val to help you remember or track?
- What process wastes your time?
- What would be useful in week 1?
- What should Val avoid touching?
""")

    write_new(client_dir / "CLIENT_ROADMAP.md", f"""
# CLIENT_ROADMAP — {display_name}

## Current status

New founder-beta client. Roadmap not yet validated.

## Month 1 candidate goals

To be defined after intake.

Possible starter lanes:
- reminders / agenda basics
- document organization
- grocery / item list
- business inventory / purchases
- meeting prep
- idea capture
- process tracking

## Month 2 candidate goals

To be defined after first usage.

## Month 3 candidate goals

To be defined after validated recurring workflow.
""")

    write_new(client_dir / "CLIENT_IDEAS.md", f"""
# CLIENT_IDEAS — {display_name}

## Open ideas

_No ideas captured yet._

## Parking / later

_No parking items yet._

## Captured ideas

_No captured ideas yet._
""")

    write_new(client_dir / "CLIENT_CAPABILITIES.md", f"""
# CLIENT_CAPABILITIES — {display_name}

Purpose:
Track capabilities active, testing, planned, and deferred for this client.

---

## Active / sealed

_None yet._

---

## Candidate capabilities to consider

### client_context_reader_v0
Status: available
Reusable from:
- Karen

### client_ideas_v0
Status: available
Reusable from:
- Karen

### grocery_list_v0 / item_list_v0 candidate
Status: available but needs client-specific adaptation
Reusable from:
- Karen

### reminders_agenda_v0
Status: testing
Reusable from:
- Karen / Val0 base

### document_inventory_v0 / carpeta_clara pattern
Status: candidate
Reusable from:
- Karen

---

## Testing / needs QA

_None yet._

---

## Planned next

Run intake and decide first activated capability.

---

## Deferred / later

_No deferred items yet._
""")

    print("CLIENT_TEMPLATE_CREATED=YES")
    print(f"client_id={client_id}")
    print(f"display_name={display_name}")
    print(f"client_type={client_type}")
    print(f"path={client_dir.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
