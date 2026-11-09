"""Verify the frozen 50-question candidate set without model calls or downloads."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.charts.dataset import load_candidate_set, sha  # noqa: E402


def verify(directory, source_dir=None):
    _, manifest, report = load_candidate_set(directory)
    inventory_path = ROOT / "data/application_filings.json"
    if sha(inventory_path.read_bytes()) != manifest["inventory_sha256"]:
        raise ValueError("Pinned application filing inventory changed.")
    inventory = {r["accession"]: r for r in json.loads(inventory_path.read_text())}
    checked = []
    for source in manifest["sources"]:
        filing = inventory[source["accession"]]
        if (source["company"] != filing["issuer"] or source["pdf_sha256"] != filing["rendition_sha256"]
                or source["pdf_url"] != filing["rendition_url"] or source["sec_source_url"] != filing["source_url"]):
            raise ValueError("Chart filing identity does not match the application inventory.")
        if source_dir is not None:
            pdf = ROOT / "data/source/aapl-2021-rendition.pdf" if source["ticker"] == "AAPL" else source_dir / f"{source['ticker']}_{source['accession']}.pdf"
            if sha(pdf.read_bytes()) != source["pdf_sha256"]:
                raise ValueError("Local original filing PDF checksum mismatch.")
            checked.append(source["accession"])
    return {**report, "filing_inventory_verified": True, "local_pdf_hashes_verified": checked,
            "local_pdf_verification_requested": source_dir is not None}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "output/chart-set-verification.json")
    args = parser.parse_args()
    try:
        report = verify(ROOT / "data/charts", args.source_dir)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"Chart candidate verification failed: {type(exc).__name__}.\n")
