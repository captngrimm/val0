from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_MAX_PAGES = 3
DEFAULT_DPI = 220
DEFAULT_LANG = "spa+eng"
OUTPUT_ROOT = Path("tmp/ocr_runtime")
WATERMARK_PHRASE = "Copia para propósitos informativos solamente"
LEGAL_MARKERS = (
    "JUZGADO",
    "AUTO",
    "OFICIO",
    "FINCA",
    "REGISTRO",
    "DEMANDA",
    "SECUESTRO",
    "EMBARGO",
    "MEDIDAS CAUTELARES",
)


@dataclass
class DocumentOCRResult:
    status: str
    pages_processed: int = 0
    combined_text: str = ""
    char_count: int = 0
    watermark_count: int = 0
    legal_marker_counts: dict[str, int] = field(default_factory=dict)
    recommendation: str = "ocr_failed"
    output_dir: str = ""
    error: str = ""
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))

    def to_dict(self) -> dict:
        return asdict(self)


def _tool(name: str) -> str | None:
    return shutil.which(name)


def ocr_tools_available() -> dict[str, bool]:
    return {
        "pdftoppm": bool(_tool("pdftoppm")),
        "tesseract": bool(_tool("tesseract")),
    }


def _run(cmd: list[str], *, timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, timeout=timeout, check=False)


def _norm(text: str) -> str:
    return " ".join(str(text or "").upper().split())


def _count_phrase(text: str, phrase: str) -> int:
    return _norm(text).count(_norm(phrase))


def _metrics(text: str) -> tuple[int, int, dict[str, int]]:
    upper = _norm(text)
    marker_counts = {marker: upper.count(marker) for marker in LEGAL_MARKERS}
    return len(text or ""), _count_phrase(text, WATERMARK_PHRASE), marker_counts


def _recommendation(text: str, *, render_ok: bool, ocr_ok: bool) -> tuple[str, str]:
    if not all(ocr_tools_available().values()):
        return "ocr_not_available", "ocr_not_available"
    if not render_ok or not ocr_ok:
        return "failed", "ocr_failed"

    char_count, watermark_count, marker_counts = _metrics(text)
    legal_hits = sum(marker_counts.values())
    if char_count >= 800 and legal_hits >= 5 and watermark_count <= max(3, legal_hits):
        return "ok", "ocr_usable"
    if char_count >= 250 and legal_hits >= 1:
        return "low_quality", "ocr_needs_review"
    return "low_quality", "ocr_needs_review"


def _safe_output_dir(pdf_path: Path, output_root: Path) -> Path:
    safe_stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", pdf_path.stem).strip("._") or "documento"
    return output_root / safe_stem


def run_pdf_ocr(
    pdf_path: str | Path,
    *,
    max_pages: int = DEFAULT_MAX_PAGES,
    dpi: int = DEFAULT_DPI,
    lang: str = DEFAULT_LANG,
    output_root: str | Path = OUTPUT_ROOT,
) -> DocumentOCRResult:
    pdf = Path(pdf_path).expanduser()
    if not pdf.exists() or not pdf.is_file():
        return DocumentOCRResult(status="file_missing", error=f"PDF not found: {pdf}")
    if pdf.suffix.lower() != ".pdf":
        return DocumentOCRResult(status="failed", error="OCR runtime currently supports PDF files only.")

    tools = ocr_tools_available()
    if not tools.get("pdftoppm") or not tools.get("tesseract"):
        return DocumentOCRResult(status="ocr_not_available", recommendation="ocr_failed", error="pdftoppm/tesseract not available")

    pages = max(1, min(int(max_pages or DEFAULT_MAX_PAGES), DEFAULT_MAX_PAGES))
    out_dir = _safe_output_dir(pdf, Path(output_root))
    out_dir.mkdir(parents=True, exist_ok=True)

    prefix = out_dir / "page"
    render_cmd = [
        _tool("pdftoppm") or "pdftoppm",
        "-f",
        "1",
        "-l",
        str(pages),
        "-r",
        str(int(dpi or DEFAULT_DPI)),
        "-png",
        str(pdf),
        str(prefix),
    ]
    try:
        render = _run(render_cmd, timeout=180)
    except Exception as exc:
        return DocumentOCRResult(status="failed", recommendation="ocr_failed", output_dir=str(out_dir), error=str(exc))

    images = sorted(out_dir.glob("page-*.png"))
    page_texts: list[str] = []
    page_reports = []
    ocr_ok = False

    for idx, image in enumerate(images, start=1):
        ocr_cmd = [_tool("tesseract") or "tesseract", str(image), "stdout", "-l", str(lang or DEFAULT_LANG), "--psm", "6"]
        try:
            ocr = _run(ocr_cmd, timeout=180)
        except Exception as exc:
            page_text = ""
            page_log = str(exc)
            rc = 1
        else:
            page_text = ocr.stdout or ""
            page_log = (ocr.stderr or "").strip()
            rc = int(ocr.returncode or 0)
        if page_text.strip():
            ocr_ok = True
        page_texts.append(page_text)
        page_file = out_dir / f"page_{idx:02d}_ocr.txt"
        page_file.write_text(page_text, encoding="utf-8")
        char_count, watermark_count, legal_marker_counts = _metrics(page_text)
        page_reports.append({
            "page": idx,
            "image": str(image),
            "text_file": str(page_file),
            "returncode": rc,
            "ocr_log": page_log,
            "char_count": char_count,
            "watermark_count": watermark_count,
            "legal_marker_counts": legal_marker_counts,
        })

    combined = "\n\n".join(page_texts).strip()
    combined_file = out_dir / "combined_ocr.txt"
    combined_file.write_text(combined, encoding="utf-8")

    char_count, watermark_count, legal_marker_counts = _metrics(combined)
    status, recommendation = _recommendation(combined, render_ok=bool(images) and render.returncode == 0, ocr_ok=ocr_ok)
    result = DocumentOCRResult(
        status=status,
        pages_processed=len(images),
        combined_text=combined,
        char_count=char_count,
        watermark_count=watermark_count,
        legal_marker_counts=legal_marker_counts,
        recommendation=recommendation,
        output_dir=str(out_dir),
        error=(render.stderr or render.stdout or "").strip() if render.returncode else "",
    )
    report = {
        **result.to_dict(),
        "combined_text_file": str(combined_file),
        "page_reports": page_reports,
        "tools": tools,
        "max_pages": pages,
        "dpi": int(dpi or DEFAULT_DPI),
        "lang": str(lang or DEFAULT_LANG),
    }
    (out_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return result
