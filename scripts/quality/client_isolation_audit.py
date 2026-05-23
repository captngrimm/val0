#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# These files are intentionally Karen-specific or explicit client registries,
# and are allowed to mention Karen/Insanity/client contact literals.
ALLOWED_KAREN_SPECIFIC_PATTERNS = (
    "core/client_identity.py",
    "core/client_contacts.py",
    "scripts/quality/client_isolation_audit.py",
    "docs/architecture/CLIENT_ISOLATION_CONTRACT_V0.md",
    "core/karen_",
    "docs/KAREN_",
    "docs/ops/",
    "docs/cleanup/KAREN_",
    "docs/lab/gcal/",
    "clients/karen/",
)

# Exact Karen-only client-zero copy that still lives in shared files during
# founder-beta. Keep this narrow: do not allow whole bot.py sections.
ALLOWED_KAREN_SPECIFIC_HITS = (
    ("bot.py", "hardcoded_vocative_insanity", "Veo varias instrucciones juntas, Insanity"),
    ("bot.py", "hardcoded_vocative_insanity", "Empezamos ordenando el caso por partes, Insanity"),
    ("bot.py", "hardcoded_vocative_insanity", "Claro, Insanity. Si tienes que llevarle documentos a la abogada"),
    ("bot.py", "hardcoded_vocative_insanity", "Insanity, antes de hablar con Nora falta revisar esto"),
    ("core/document_summary_queries.py", "hardcoded_vocative_insanity", "Insanity, aquí va ordenado para hablar con la abogada"),
)

SCAN_EXTS = {".py", ".md", ".json", ".txt"}

FORBIDDEN_REUSABLE_PATTERNS = [
    ("hardcoded_vocative_insanity", re.compile(r"\bInsanity\b")),
    ("hardcoded_client_id_karen_kwarg", re.compile(r"client_id\s*=\s*[\"']karen[\"']")),
    ("hardcoded_client_ref_karen", re.compile(r"CLIENT:karen")),
    ("hardcoded_clients_karen_path", re.compile(r"/clients/karen\b")),
]

# Literal "karen" in bot.py/core/client_* is suspicious but not fatal yet.
WARN_PATTERNS = [
    ("literal_karen", re.compile(r"[\"']karen[\"']")),
    ("karen_email", re.compile(r"karenmm20", re.IGNORECASE)),
]

def is_allowed(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    return any(rel.startswith(p) for p in ALLOWED_KAREN_SPECIFIC_PATTERNS)

def is_allowed_hit(rel: str, name: str, line_text: str) -> bool:
    return any(
        rel == allowed_rel and name == allowed_name and snippet in line_text
        for allowed_rel, allowed_name, snippet in ALLOWED_KAREN_SPECIFIC_HITS
    )

def should_scan(path: Path) -> bool:
    if ".git" in path.parts or ".venv" in path.parts or "__pycache__" in path.parts:
        return False
    if path.suffix not in SCAN_EXTS:
        return False
    return True

def main() -> int:
    errors = []
    warnings = []

    for path in ROOT.rglob("*"):
        if not path.is_file() or not should_scan(path):
            continue

        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8", errors="ignore")

        if is_allowed(path):
            continue

        for name, rx in FORBIDDEN_REUSABLE_PATTERNS:
            for m in rx.finditer(text):
                line_no = text.count("\n", 0, m.start()) + 1
                line_text = text.splitlines()[line_no - 1] if line_no > 0 else ""
                if is_allowed_hit(rel, name, line_text):
                    continue
                errors.append((name, rel, line_no, m.group(0)))

        # Warnings only in likely reusable areas.
        if rel == "bot.py" or rel.startswith("core/client_"):
            for name, rx in WARN_PATTERNS:
                for m in rx.finditer(text):
                    line_no = text.count("\n", 0, m.start()) + 1
                    warnings.append((name, rel, line_no, m.group(0)))

    if warnings:
        print("=== CLIENT ISOLATION WARNINGS ===")
        for name, rel, line_no, hit in warnings[:200]:
            print(f"WARN {name}: {rel}:{line_no}: {hit}")

    if errors:
        print("=== CLIENT ISOLATION ERRORS ===")
        for name, rel, line_no, hit in errors[:200]:
            print(f"ERROR {name}: {rel}:{line_no}: {hit}")
        print(f"\nFAIL: {len(errors)} hard client-isolation violations found.")
        return 1

    print("PASS: no hard client-isolation violations found outside allowed Karen-specific files.")
    if warnings:
        print(f"Warnings remain: {len(warnings)}. These should be migrated before multi-client expansion.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
