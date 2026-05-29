#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.document_summary_queries import (  # noqa: E402
    _looks_like_watermark_dominated_text,
    _watermark_guard_reply,
)

watermark_text = "Copia para propositos informativos solamente\n" * 9
assert _looks_like_watermark_dominated_text(watermark_text), "repeated watermark should be blocked"

normal_text = """
JUZGADO PRIMERO DE CIRCUITO DE LO CIVIL.
AUTO No. 944.
Se admite demanda ordinaria de prescripción adquisitiva de dominio.
Finca 10082, Distrito de Arraiján, Provincia de Panamá.
"""
assert not _looks_like_watermark_dominated_text(normal_text), "normal legal text should not be blocked"

reply = _watermark_guard_reply("Auto secuestro Embargo o Medidas Cautelares Juncá.pdf")
assert "necesita OCR o revisión visual" in reply
assert "Copia para propósitos informativos solamente" in reply
assert "no debo generar un resumen" in reply

source = (ROOT / "core" / "document_summary_queries.py").read_text()
assert "_looks_like_watermark_dominated_doc" in source
assert "_watermark_guard_reply(filename)" in source

print("PASS: Karen document watermark guard smoke cases passed.")
