#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.document_summary_queries import (  # noqa: E402
    _looks_like_watermark_dominated_saved_summary,
    _watermark_guard_reply,
)

bad = "Copia para propositos informativos solamente " * 8
good = "Auto No. 944. Proceso ordinario de prescripción adquisitiva de dominio. Finca 10082."

assert _looks_like_watermark_dominated_saved_summary(bad), "saved watermark summary should be blocked"
assert not _looks_like_watermark_dominated_saved_summary(good), "real legal summary should not be blocked"

reply = _watermark_guard_reply("Auto_secuestro_Embargo_o_Medidas_Cautelares_Junc_.pdf")
assert "necesita OCR o revisión visual" in reply
assert "marca de agua" in reply

source = (ROOT / "core" / "document_summary_queries.py").read_text()
assert "_looks_like_watermark_dominated_saved_summary" in source
assert "resumen guardado parece marca de agua" in source
assert "if _looks_like_watermark_dominated_saved_summary(saved_summary):" in source
assert 'return _watermark_guard_reply(filename or display_title or "documento")' in source
assert "await _reply_text_chunked(update, reply)" in source

print("PASS: Karen saved-summary watermark guard smoke cases passed.")
