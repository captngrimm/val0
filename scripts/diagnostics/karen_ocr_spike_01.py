#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path


WATERMARK = "Copia para propósitos informativos solamente"
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
OUT_DIR = Path("tmp/ocr_spike_01")


def _tool(name: str) -> str | None:
    return shutil.which(name)


def _run(cmd: list[str], *, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, timeout=timeout, check=False)


def _norm(text: str) -> str:
    return " ".join(str(text or "").upper().split())


def _count_phrase(text: str, phrase: str) -> int:
    return _norm(text).count(_norm(phrase))


def _metrics(text: str) -> dict:
    upper = _norm(text)
    return {
        "character_count": len(text or ""),
        "watermark_count": _count_phrase(text, WATERMARK),
        "legal_marker_counts": {marker: upper.count(marker) for marker in LEGAL_MARKERS},
    }


def _recommend(combined_text: str, tools: dict[str, bool], render_ok: bool, ocr_ok: bool) -> str:
    if not tools.get("tesseract") or not tools.get("pdftoppm"):
        return "ocr_not_available"
    if not render_ok or not ocr_ok:
        return "ocr_failed"
    metrics = _metrics(combined_text)
    legal_hits = sum(metrics["legal_marker_counts"].values())
    chars = metrics["character_count"]
    watermark = metrics["watermark_count"]
    if chars >= 800 and legal_hits >= 5 and watermark <= max(3, legal_hits):
        return "ocr_usable"
    if chars >= 200 and legal_hits >= 1:
        return "ocr_needs_preprocessing"
    return "ocr_failed"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def render_pages(pdf: Path, out_dir: Path, pages: int, dpi: int) -> tuple[list[Path], str]:
    pdftoppm = _tool("pdftoppm")
    if not pdftoppm:
        return [], "pdftoppm not available"
    prefix = out_dir / "page"
    cmd = [pdftoppm, "-f", "1", "-l", str(pages), "-r", str(dpi), "-png", str(pdf), str(prefix)]
    result = _run(cmd, timeout=180)
    images = sorted(out_dir.glob("page-*.png"))
    return images, (result.stderr or result.stdout or "").strip()


def ocr_image(image: Path, lang: str) -> tuple[str, str]:
    tesseract = _tool("tesseract")
    if not tesseract:
        return "", "tesseract not available"
    cmd = [tesseract, str(image), "stdout", "-l", lang, "--psm", "6"]
    result = _run(cmd, timeout=180)
    if result.returncode != 0:
        return "", (result.stderr or result.stdout or f"tesseract rc={result.returncode}").strip()
    return result.stdout or "", (result.stderr or "").strip()


def pdftotext_sample(pdf: Path, out_dir: Path, pages: int) -> tuple[str, str]:
    pdftotext = _tool("pdftotext")
    if not pdftotext:
        return "", "pdftotext not available"
    out = out_dir / "pdftotext_first_pages.txt"
    cmd = [pdftotext, "-f", "1", "-l", str(pages), str(pdf), str(out)]
    result = _run(cmd, timeout=60)
    text = out.read_text(encoding="utf-8", errors="replace") if out.exists() else ""
    return text, (result.stderr or result.stdout or "").strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnostic OCR spike for Karen Registro Público/court PDFs.")
    parser.add_argument("pdf_path", help="Path to a PDF to inspect.")
    parser.add_argument("--pages", type=int, default=3, help="Number of first pages to render/OCR, default 3.")
    parser.add_argument("--dpi", type=int, default=220, help="Render DPI for pdftoppm, default 220.")
    parser.add_argument("--lang", default="spa+eng", help="Tesseract languages, default spa+eng.")
    args = parser.parse_args()

    pdf = Path(args.pdf_path).expanduser().resolve()
    if not pdf.exists() or not pdf.is_file():
        raise SystemExit(f"PDF not found: {pdf}")

    pages = max(1, min(int(args.pages or 3), 3))
    out_dir = OUT_DIR / pdf.stem
    out_dir.mkdir(parents=True, exist_ok=True)

    tools = {
        "pdftoppm": bool(_tool("pdftoppm")),
        "pdftotext": bool(_tool("pdftotext")),
        "tesseract": bool(_tool("tesseract")),
        "ocrmypdf": bool(_tool("ocrmypdf")),
    }

    pdftotext_text, pdftotext_log = pdftotext_sample(pdf, out_dir, pages)
    _write(out_dir / "pdftotext_first_pages.txt", pdftotext_text)

    images, render_log = render_pages(pdf, out_dir, pages, int(args.dpi or 220))
    page_texts: list[str] = []
    page_reports: list[dict] = []
    ocr_ok = False
    for idx, image in enumerate(images, start=1):
        text, log = ocr_image(image, str(args.lang or "spa+eng"))
        page_texts.append(text)
        if text.strip():
            ocr_ok = True
        _write(out_dir / f"page_{idx:02d}_ocr.txt", text)
        page_reports.append({
            "page": idx,
            "image": str(image),
            "text_file": str(out_dir / f"page_{idx:02d}_ocr.txt"),
            "ocr_log": log,
            "metrics": _metrics(text),
        })

    combined = "\n\n".join(page_texts)
    _write(out_dir / "combined_ocr.txt", combined)

    report = {
        "pdf": str(pdf),
        "output_dir": str(out_dir),
        "pages_requested": pages,
        "tools": tools,
        "render_log": render_log,
        "pdftotext_log": pdftotext_log,
        "pdftotext_metrics": _metrics(pdftotext_text),
        "ocr_metrics": _metrics(combined),
        "page_reports": page_reports,
        "recommendation": _recommend(combined, tools, bool(images), ocr_ok),
    }
    _write(out_dir / "report.json", json.dumps(report, ensure_ascii=False, indent=2))

    print(json.dumps({
        "pdf": str(pdf),
        "output_dir": str(out_dir),
        "tools": tools,
        "ocr_metrics": report["ocr_metrics"],
        "pdftotext_metrics": report["pdftotext_metrics"],
        "recommendation": report["recommendation"],
    }, ensure_ascii=False, indent=2))
    return 0 if report["recommendation"] != "ocr_failed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
