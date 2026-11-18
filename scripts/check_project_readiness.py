"""R1/R2/R7/R11/R12: reproduce application coverage and expose actual study gates.

Automated source/index checks are not independent human acceptance. Never writes
approval records. The generated public snapshot contains no private configuration.
"""
import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.audit_corpus_candidates import audit_candidates  # noqa: E402
from src.benchmark.gates import evaluate_gates  # noqa: E402
from src.indexing.store import ExactStore  # noqa: E402
from src.workspace_corpus import checked_workspace_records  # noqa: E402


def check(root=ROOT, corpus=None):
    root = Path(root)
    corpus = Path(corpus or root / "output/nov17/corpus")
    output = root / "output/final-checks"
    output.mkdir(parents=True, exist_ok=True)
    audit = audit_candidates(corpus / "coverage.json", output / "source-audit.json")
    registry = json.loads((root / "data/application_filings.json").read_text())
    if not audit["automated_checks_passed"]:
        raise ValueError("Source/package audit failed; inspect output/final-checks/source-audit.json")
    stores = {v: ExactStore(corpus / v) for v in "ABC"}
    records = checked_workspace_records(root, corpus, stores["C"])
    ledger = json.loads((corpus / "coverage.json").read_text())
    rows = {r["accession"]: r for r in ledger["filings"]}
    for variant, store in stores.items():
        expected = []
        for accession in sorted(store.catalog["filings"]):
            package = json.loads((corpus / "records" / f"{accession}.json").read_text())
            if store.catalog["filings"][accession] != rows[accession]["generations"][variant]:
                raise ValueError("Index generation differs from coverage ledger")
            expected.extend(package["variants"][variant]["records"])
        if store.records != expected:
            raise ValueError("Matched index records differ from parsed packages")
    supported = {r["metadata"]["accession"] for r in records}
    tickers = {r["ticker"] for r in registry if r["accession"] in supported}
    counts = {t: sum(f["ticker"] == t and f["accession"] in supported for f in registry) for t in tickers}
    gates = evaluate_gates(root)
    for info in gates.values():
        info["reasons"] = [reason.replace(str(root), ".") for reason in info["reasons"]]
    result = {"generated_at_utc": datetime.now(UTC).isoformat(),
              "coverage": {"declared": len(registry), "source_checked": audit["passed_filings"],
                           "connected": len(supported), "companies": len(tickers), "by_company": counts,
                           "prd_application_counts_met": counts.get("AAPL", 0) >= 5 and counts.get("MSFT", 0) >= 5 and len(tickers) >= 10,
                           "independently_accepted": ledger["independently_accepted_canonical_filings"],
                           "canonical_records": len(records), "matched_indexes": {v: len(s.records) for v, s in stores.items()}},
              "experiments": {"status": "acceptance_required", "gates": gates,
                              "final_matrix_completed": 0, "final_matrix_required": 28,
                              "independent_output_audit_completed": 0, "independent_output_audit_required": 50,
                              "manual_requirements": ["Eligible independent source and chart-question/caption decisions on original sources",
                                  "Hash-bound gate acceptance and development routing freeze",
                                  "Review official source-equivalent benchmark bindings before complete A-G/RAGAS/Llama runs",
                                  "Independent predeclared fifty-output audit after actual final runs"],
                              "note": "No completed final run ledger or independent acceptance exists. Tests and application probes are separate."},
              "filings": [{**f, "processing_status": "source_checked_indexed" if f["accession"] in supported else "processing_required",
                           "records": rows.get(f["accession"], {}).get("candidate_counts", {}).get("C", 0),
                           "independent_acceptance": rows.get(f["accession"], {}).get("independent_acceptance", "pending")}
                          for f in registry],
              "inputs": {"coverage_sha256": hashlib.sha256((corpus / "coverage.json").read_bytes()).hexdigest()}}
    (output / "readiness.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path)
    parser.add_argument("--publish-web", action="store_true")
    args = parser.parse_args()
    result = check(corpus=args.corpus)
    if args.publish_web:
        web = ROOT / "web/data"
        (web / "filings.json").write_text(json.dumps(result["filings"], indent=2) + "\n")
        (web / "project-status.json").write_text(json.dumps({k: v for k, v in result.items() if k != "filings"}, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "filings"}, indent=2))
    return int(not result["coverage"]["prd_application_counts_met"])


if __name__ == "__main__":
    raise SystemExit(main())
