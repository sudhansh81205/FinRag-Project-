"""Build the offline November 4 evidence package from pinned source renditions."""

import argparse
import gzip
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.parse_filing import json_bytes, write_atomic  # noqa: E402
from src.ingestion.filing_parser import ParseError, parse_filing, sha256, validate_source  # noqa: E402
from src.ingestion.pdf_evidence import corroborate_pdf, original_chart  # noqa: E402
from src.ingestion.statement_cells import statement_cells  # noqa: E402


def prepare(output):
    manifest = json.loads((ROOT / "data/filing_manifest.json").read_text())
    archive = (ROOT / manifest["source_archive"]).read_bytes()
    if sha256(archive) != manifest["source_archive_sha256"]:
        raise ParseError("Archive checksum mismatch")
    raw = gzip.decompress(archive)
    narrative, parents, _ = parse_filing(raw, manifest)
    soup = validate_source(raw, manifest)
    cells = statement_cells(soup, parents)
    spec = json.loads((ROOT / "data/source/apple-2021-renditions.json").read_text())
    if spec["accession"] != manifest["accession"]:
        raise ParseError("HTML and PDF rendition accessions differ")
    pdf_path = ROOT / spec["path"]
    checks = corroborate_pdf(pdf_path, spec, cells)
    image = original_chart(pdf_path, spec, soup)
    asset_name = sha256(image) + ".jpg"
    chart = {
        **spec["chart"],
        "id": f"{manifest['accession']}:chart:{sha256(image)}",
        "asset": asset_name,
        "accession": manifest["accession"],
        "pdf_url": spec["url"],
        "pdf_sha256": spec["sha256"],
        "html_url": manifest["source_url"],
        "html_sha256": manifest["raw_sha256"],
    }
    package = {
        "accession": manifest["accession"],
        "schema_version": "nov04-local-v1",
        "narratives": narrative,
        "parent_tables": parents,
        "cells": cells,
        "pdf_corroboration": checks,
        "chart_sources": [chart],
    }
    write_atomic(output / asset_name, image)
    write_atomic(output / "evidence.json", json_bytes(package))
    return {
        key: len(package[key])
        for key in ("narratives", "parent_tables", "cells", "pdf_corroboration", "chart_sources")
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "data/processed/nov04")
    try:
        print(json.dumps(prepare(parser.parse_args().output), indent=2))
    except (ParseError, OSError) as exc:
        parser.exit(1, f"Evidence preparation failed: {exc}\n")
