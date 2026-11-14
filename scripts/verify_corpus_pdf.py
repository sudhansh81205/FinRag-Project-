"""Corroborate pinned Apple 2022–25 PDF sales rows against SEC HTML cells."""

import argparse
import json
import sys
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.acquire_corpus import acquire  # noqa: E402
from scripts.parse_filing import json_bytes, write_atomic  # noqa: E402
from src.ingestion.filing_parser import ParseError  # noqa: E402
from src.ingestion.pdf_evidence import corroborate_pdf  # noqa: E402

PAGES = {
    "0000320193-22-000108": 32,
    "0000320193-23-000106": 31,
    "0000320193-24-000123": 32,
    "0000320193-25-000079": 32,
}
TITLE = "CONSOLIDATED STATEMENTS OF OPERATIONS"


def validate_position(check, page, years):
    # pdfplumber extracts independent coordinates with a top-left origin.
    words = page.extract_words()
    height, width = float(page.height), float(page.width)
    line_hits = [
        line
        for line in page.extract_text_lines()
        if line["text"].strip().startswith(check["row_label"] + " ")
    ]
    if len(line_hits) != 1:
        raise ParseError("PDF row label is ambiguous")
    line = line_hits[0]
    headers = {}
    for year in years:
        hits = [w for w in words if w["text"] == year and w["bottom"] < line["top"]]
        if not hits:
            raise ParseError("Independent PDF year header missing")
        headers[year] = max(hits, key=lambda w: w["bottom"])
    if max(w["top"] for w in headers.values()) - min(w["top"] for w in headers.values()) > 1:
        raise ParseError("Independent PDF year headers do not share a line")
    for span in check["source_spans"]:
        if span["origin"] != "BOTTOMLEFT":
            raise ParseError("Unsupported Docling coordinate origin")
        x0, y0, x1, y1 = span["bbox"]
        if not (0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height):
            raise ParseError("Invalid PDF span bounds")
        top, bottom = height - y1, height - y0
        matches = [
            w
            for w in words
            if w["text"] == span["text"]
            and abs(w["x0"] - x0) < 1
            and abs(w["x1"] - x1) < 1
            and abs(w["top"] - top) < 1
            and abs(w["bottom"] - bottom) < 1
        ]
        if len(matches) != 1 or not (line["top"] - 1 <= top < bottom <= line["bottom"] + 1):
            raise ParseError("Independent PDF word/row coordinates disagree")
        centers = {y: (w["x0"] + w["x1"]) / 2 for y, w in headers.items()}
        closest = min(centers, key=lambda y: abs((x0 + x1) / 2 - centers[y]))
        if closest != check["column_header"]:
            raise ParseError("Independent PDF year column disagrees")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=ROOT / "output/nov13")
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args()
    filings = json.loads((ROOT / "data/application_filings.json").read_bytes())
    ledger = []
    for filing in filings:
        if (accession := filing["accession"]) not in PAGES:
            continue
        source = acquire(filing, download=args.download)
        row = {"accession": accession, "source": source, "status": "failed"}
        ledger.append(row)
        if source["status"] != "downloaded_identity_checked":
            continue
        try:
            data = json.loads((args.corpus / "records" / (accession + ".json")).read_bytes())
            cells = [
                {
                    **r,
                    "metadata": {
                        **r["metadata"],
                        "table_title": TITLE,
                        "column_header": r["metadata"]["column_header"][:4],
                    },
                }
                for r in data["cells"]
                if r["metadata"]["table_title"] == "Income statement"
            ]
            page = PAGES[accession]
            path = ROOT / filing["rendition_path"]
            checks = corroborate_pdf(
                path,
                {
                    "sha256": filing["rendition_sha256"],
                    "statement_pages": [
                        {
                            "page": page,
                            "title": TITLE,
                            "checked_rows": ["Total net sales"],
                        }
                    ],
                },
                cells,
            )
            with pdfplumber.open(path) as pdf:
                for check in checks:
                    validate_position(
                        check, pdf.pages[page - 1], [c["column_header"] for c in checks]
                    )
            row["checks"] = checks
            row["status"] = "matched_html_and_pdf_extractors"
        except (ValueError, OSError) as exc:
            row["error"] = str(exc)
    write_atomic(args.corpus / "pdf-checks.json", json_bytes(ledger))
    for row in ledger:
        print(row["accession"], row["status"], row.get("error", ""))
    return int(any(row["status"] != "matched_html_and_pdf_extractors" for row in ledger))


if __name__ == "__main__":
    raise SystemExit(main())
