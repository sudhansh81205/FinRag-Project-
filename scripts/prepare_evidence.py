"""Build the offline November 4 evidence package from pinned source renditions."""

import argparse
import gzip
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.parse_filing import json_bytes, write_atomic  # noqa: E402
from src.contracts import canonical_record  # noqa: E402
from src.ingestion.filing_parser import ParseError, parse_filing, sha256, validate_source  # noqa: E402
from src.ingestion.pdf_evidence import corroborate_pdf, original_chart  # noqa: E402
from src.ingestion.statement_cells import statement_cells  # noqa: E402


def validate_records(records, schema):
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    identities = set()
    for record in records:
        errors = list(validator.iter_errors(record))
        if errors:
            raise ParseError(f"Canonical schema mismatch at {list(errors[0].absolute_path)}")
        identity = record["evidence_id"]
        if identity in identities:
            raise ParseError("Duplicate canonical evidence identity")
        identities.add(identity)
        if sha256(record["content"].encode("utf-8")) != record["metadata"]["content_sha256"]:
            raise ParseError("Canonical content hash mismatch")


def prepare(output):
    manifest = json.loads((ROOT / "data/filing_manifest.json").read_text())
    archive = (ROOT / manifest["source_archive"]).read_bytes()
    if sha256(archive) != manifest["source_archive_sha256"]:
        raise ParseError("Archive checksum mismatch")
    raw = gzip.decompress(archive)
    narrative, parents, _ = parse_filing(raw, manifest)
    soup = validate_source(raw, manifest)
    cells = statement_cells(soup, parents)
    narrative = [canonical_record(r) for r in narrative]
    parents = [canonical_record(r) for r in parents]
    records = narrative + parents + cells
    schema_bytes = (ROOT / "data/contracts/canonical_record.schema.json").read_bytes()
    validate_records(records, json.loads(schema_bytes))
    spec = json.loads((ROOT / "data/source/apple-2021-renditions.json").read_text())
    if spec["accession"] != manifest["accession"]:
        raise ParseError("HTML and PDF rendition accessions differ")
    pdf_path = ROOT / spec["path"]
    checks = corroborate_pdf(pdf_path, spec, cells)
    image = original_chart(pdf_path, spec, soup)
    asset_name = sha256(image) + ".jpg"
    chart = {
        **spec["chart"],
        "source_asset_id": f"{manifest['accession']}:chart:{sha256(image)}",
        "asset": asset_name,
        "accession": manifest["accession"],
        "pdf_url": spec["url"],
        "pdf_sha256": spec["sha256"],
        "html_url": manifest["source_url"],
        "html_sha256": manifest["raw_sha256"],
    }
    package = {
        "accession": manifest["accession"],
        "schema_version": "nov04-canonical-v1",
        "record_schema_sha256": sha256(schema_bytes),
        "narratives": narrative,
        "parent_tables": parents,
        "cells": cells,
        "pdf_corroboration": checks,
        "chart_sources": [chart],
    }
    # Retain a self-contained HTML snapshot alongside the records for source audit.
    for record in records:
        record["metadata"]["source_file"] = "source.html"
    payload = json_bytes(package)
    ordered_ids = [r["evidence_id"] for r in narrative + cells]
    build_manifest = {
        "schema_version": 1,
        "profile": "apple-2021-cells-pdf-chart-sources",
        "record_schema_sha256": sha256(schema_bytes),
        "record_count": len(records),
        "candidate_count": len(ordered_ids),
        "ordered_candidate_ids_sha256": sha256(
            json.dumps(ordered_ids, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        ),
        "files_sha256": {
            "evidence.json": sha256(payload),
            "source.html": sha256(raw),
            asset_name: sha256(image),
        },
        "pdf_source": {"path": spec["path"], "sha256": spec["sha256"]},
        "independent_source_audit": "pending",
        "index_ready": False,
    }
    payloads = {"source.html": raw, asset_name: image, "evidence.json": payload,
                "manifest.json": json_bytes(build_manifest)}
    # Published generations are immutable. A new/changed filing must use a new
    # directory; neither another filing nor a partially changed package is erased.
    if output.is_symlink():
        raise ParseError("Evidence destination must not be a symbolic link")
    if output.exists() and any(output.iterdir()):
        if {p.name for p in output.iterdir()} != set(payloads) or any(
            (output / name).is_symlink() or not (output / name).is_file()
            or (output / name).read_bytes() != data for name, data in payloads.items()
        ):
            raise ParseError("Destination differs from this generation; choose a fresh output directory")
    else:
        for name, data in payloads.items():
            write_atomic(output / name, data)
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
