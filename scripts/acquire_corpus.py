"""Acquire pinned PDF renditions and report raw coverage separately from indexing.

AnnualReports copies are explicitly mirrors. SEC filing identity remains separate.
Acquisition is not a semantic source audit or a general PDF table parser.
"""

import argparse
import io
import json
import re
import sys
from datetime import date
from pathlib import Path

import requests
from pypdf import PdfReader
from pypdf.errors import PyPdfError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.parse_filing import json_bytes, write_atomic  # noqa: E402
from src.contracts import sha256, within  # noqa: E402


def inspect_pdf(payload, filing):
    if not payload.startswith(b"%PDF"):
        raise ValueError("Response is not a PDF")
    reader = PdfReader(io.BytesIO(payload))
    # Annual report covers/letters may precede the filing cover. Match the exact
    # company, form and period on a page, without treating the annual label as proof.
    period = date.fromisoformat(filing["period_end"])
    date_pattern = rf"{period.strftime('%B')}\s+0?{period.day},?\s+{period.year}"
    company = re.sub(r"\W", "", filing["issuer"]).lower()
    evidence = []
    for i, page in enumerate(reader.pages):
        text = re.sub(r"\s+", " ", page.extract_text() or "")
        compact = re.sub(r"\W", "", text).lower()
        if (
            company in compact
            and re.search(r"form\s*10\s*[-–]?\s*k", text, re.I)
            and re.search(r"(?:fiscal\s+)?year\s+ended\s+" + date_pattern, text, re.I)
        ):
            evidence.append(i + 1)
            break
        if i >= 30:
            break
    if not evidence:
        raise ValueError("Exact issuer/form/period not found in the first 31 pages")
    return {
        "page_count": len(reader.pages),
        "identity_pages": evidence,
        "identity_check": "issuer_form_period_text",
        "byte_sha256": sha256(payload),
    }


def acquire(filing, *, download=False):
    result = {
        "accession": filing["accession"],
        "ticker": filing["ticker"],
        "period_end": filing["period_end"],
        "source_url": filing["source_url"],
        "rendition_url": filing["rendition_url"],
        "path": filing["rendition_path"],
        "status": "failed",
        "canonical_parsed_records": 0,
        "indexed_records": 0,
        "chart_availability": "not_audited",
        "parser_status": "unsupported_by_apple_html_profile",
    }
    try:
        path = within(ROOT, filing["rendition_path"])
        if path.is_file():
            payload = path.read_bytes()
        elif download:
            response = requests.get(
                filing["rendition_url"],
                timeout=60,
                headers={"User-Agent": "FinRAG academic filing research"},
            )
            if response.status_code != 200:
                return {**result, "failure": f"http_{response.status_code}"}
            payload = response.content
        else:
            return {**result, "status": "missing", "failure": "run_with_download"}
        digest = sha256(payload)
        if filing.get("rendition_sha256") and digest != filing["rendition_sha256"]:
            raise ValueError("Pinned rendition checksum mismatch")
        result.update(inspect_pdf(payload, filing), status="downloaded_identity_checked")
        if not path.exists():
            write_atomic(path, payload)
    except (OSError, ValueError, PyPdfError, requests.RequestException) as exc:
        result["failure"] = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT / "output/corpus/acquisition.json")
    args = parser.parse_args(argv)
    filings = json.loads((ROOT / "data/application_filings.json").read_bytes())
    rows = []
    for filing in filings:
        row = acquire(filing, download=args.download)
        rows.append(row)
        print(f"{row['ticker']} {row['period_end']}: {row['status']}", flush=True)
    report = {
        "profile": "raw_rendition_acquisition_not_index_acceptance",
        "filings": rows,
        "inventoried_filings": len(rows),
        "inventoried_companies": len({r["ticker"] for r in rows}),
        "downloaded_identity_checked": sum(
            r["status"] == "downloaded_identity_checked" for r in rows
        ),
        "note": "Parsed/indexed counts here are zero: this command only inventories PDF sources. See the separate actual index report for accepted HTML records.",
    }
    write_atomic(args.output, json_bytes(report))
    return 0 if report["downloaded_identity_checked"] == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
