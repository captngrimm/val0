# OCR SPIKE 01: Registro Publico PDF Feasibility

Date: 2026-05-31

This is a diagnostic spike, not runtime OCR. It does not wire OCR into Val's document pipeline and does not change document summary behavior.

## Why

Karen's Registro Publico / court PDFs can contain visible legal text as scanned page images, while parsed text is dominated by:

`Copia para propositos informativos solamente`

Val currently refuses fake summaries for watermark-dominated extraction. This spike checks whether local OCR can recover useful visible text.

## Local Tooling Detected

- `pdftoppm`: available at `/usr/bin/pdftoppm`
- `pdftotext`: available at `/usr/bin/pdftotext`
- `tesseract`: available at `/usr/bin/tesseract`
- Tesseract languages: `spa`, `eng`, `osd`
- `ocrmypdf`: available at `/usr/bin/ocrmypdf`
- Python libraries checked: `PIL`, `pdf2image`, `pypdf` available; `fitz` not installed

## Diagnostic Script

Run:

```bash
python3 scripts/diagnostics/karen_ocr_spike_01.py /path/to/document.pdf
```

Optional:

```bash
python3 scripts/diagnostics/karen_ocr_spike_01.py /path/to/document.pdf --pages 3 --dpi 220 --lang spa+eng
```

The script writes local diagnostic outputs under:

`tmp/ocr_spike_01/`

Outputs include rendered page images, OCR text per page, combined OCR text, and `report.json` with watermark/legal-marker metrics.

## Sample Candidate Found Locally

One likely Karen sample found during the spike:

`/opt/val0/vfms_data/raw/20260531_000001__10200__Auto_secuestro_Embargo_o_Medidas_Cautelares_Junc_.pdf`

Do not paste full OCR output into product docs. Use the local `tmp/` report for diagnosis.

## Local Spike Result

Command run:

```bash
python3 scripts/diagnostics/karen_ocr_spike_01.py /opt/val0/vfms_data/raw/20260531_000001__10200__Auto_secuestro_Embargo_o_Medidas_Cautelares_Junc_.pdf --pages 3
```

Result:

- Recommendation: `ocr_usable`
- OCR characters: 6,725
- Watermark count in OCR text: 0
- Legal marker hits included: `JUZGADO`, `AUTO`, `OFICIO`, `REGISTRO`, `DEMANDA`
- Embedded `pdftotext` characters for the same page window: 227

Short redacted OCR sample:

```text
JUDICIAL
JUZGADO PRIMERO DE CIRCUITO DE LO CIVIL
DEL TERCER CIRCUITO JUDICIAL DE PANAMA.
OFICIO No. [redacted]
La Chorrera, 23 de mayo del 2022
Registro Publico.
Para los fines legales consiguientes remito a usted copia debidamente
autenticada del Auto No. [redacted]
```

## Recommendation Categories

- `ocr_usable`: OCR recovered enough legal signal for a future summary lane.
- `ocr_needs_preprocessing`: OCR found some signal, but image cleanup/page segmentation may be needed.
- `ocr_not_available`: required local tools are missing.
- `ocr_failed`: tools ran but did not recover usable text.

## Next Step

If the spike reports `ocr_usable` or `ocr_needs_preprocessing` on Karen's real Registro Publico PDFs, the next product task should design a guarded OCR lane:

- explicit OCR status in inventory
- no fake legal summaries
- OCR text provenance separated from embedded PDF text
- summary only after text-quality checks
- no runtime OCR until deliberately scoped
