"""R1/R2/R3/R13: reproduce sources/packages without manufacturing human acceptance.

A successful automated byte/schema/count check is review preparation. Historical
November15 reports are preserved. Original-source interpretation and independent
human approval are separate from these checks.
"""

import argparse
import gzip
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.indexing.store import validate_records  # noqa: E402


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def audit_candidates(coverage_path, output_path):
    coverage_path, output_path = Path(coverage_path), Path(output_path)
    coverage = json.loads(coverage_path.read_bytes())
    profiles_path = ROOT / "data/corpus_html_profiles.json"
    profiles = json.loads(profiles_path.read_bytes())
    filings = {r["accession"]: r for r in json.loads((ROOT / "data/application_filings.json").read_bytes())}
    rows, seen = [], set()
    for row in coverage["filings"]:
        accession = row["accession"]
        errors = []
        if accession in seen:
            raise ValueError("Duplicate filing in coverage ledger")
        seen.add(accession)
        profile = profiles[accession]
        raw = gzip.decompress((ROOT / "data/source/corpus" / f"{accession}.html.gz").read_bytes())
        source_hashes = {"html": sha256(raw)}
        if source_hashes["html"] != profile["sha256"]:
            errors.append("Pinned source HTML hash mismatch")
        if exhibit := profile.get("exhibit"):
            payload = gzip.decompress((ROOT / "data/source/corpus" / (exhibit["filename"] + ".gz")).read_bytes())
            source_hashes["exhibit_html"] = sha256(payload)
            if source_hashes["exhibit_html"] != exhibit["sha256"]:
                errors.append("Pinned exhibit hash mismatch")
        filing = filings[accession]
        if any(row.get(k) != filing[k] for k in ("ticker", "issuer", "period_end", "source_url")):
            errors.append("Coverage filing identity mismatch")
        package_path = coverage_path.parent / "records" / f"{accession}.json"
        payload = package_path.read_bytes()
        package = json.loads(payload)
        if sha256(payload) != row.get("package_sha256"):
            errors.append("Parsed package changed since coverage was recorded")
        if any(package.get("source_sha256", {}).get(k) != v for k, v in source_hashes.items()):
            errors.append("Package bound to different source bytes")
        counts = {}
        for variant in "ABC":
            records = package["variants"][variant]["records"]
            parents = package["variants"][variant]["parents"]
            validate_records(records, parents)
            counts[variant] = len(records)
        if counts != row.get("candidate_counts"):
            errors.append("Actual variant counts differ from coverage ledger")
        if len(package["cells"]) != row.get("cells") or len(package["parents"]) != row.get("parent_tables"):
            errors.append("Actual cell/parent counts differ from coverage ledger")
        rows.append({"accession": accession, "ticker": filing["ticker"],
                     "source_hashes": source_hashes, "package_sha256": sha256(payload),
                     "counts": counts, "cells": len(package["cells"]),
                     "parents": len(package["parents"]), "automated_checks_passed": not errors,
                     "errors": errors, "independent_human_acceptance": "not_established"})
    report = {
        "schema_version": 2, "audit_type": "automated_source_and_package_reproduction",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "coverage_sha256": sha256(coverage_path.read_bytes()),
        "profiles_sha256": sha256(profiles_path.read_bytes()),
        "declared_filings": len(filings), "checked_filings": len(rows),
        "passed_filings": sum(r["automated_checks_passed"] for r in rows),
        "all_declared_filings_present": seen == set(filings), "filings": rows,
        "automated_checks_passed": bool(rows) and seen == set(filings) and all(r["automated_checks_passed"] for r in rows),
        "independent_human_acceptance": "not_established", "index_acceptance": "not_established",
        "note": "Automated predicates do not identify a human reviewer, certify source interpretation or open final experiment gates.",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coverage", type=Path, default=ROOT / "output/nov17/corpus/coverage.json")
    parser.add_argument("--output", type=Path, default=ROOT / "output/nov17/corpus/reproduction_audit.json")
    args = parser.parse_args()
    report = audit_candidates(args.coverage, args.output)
    print(json.dumps({k: v for k, v in report.items() if k != "filings"}, indent=2))
    return int(not report["automated_checks_passed"])


if __name__ == "__main__":
    raise SystemExit(main())
