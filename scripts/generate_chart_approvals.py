"""Generate Ujjwal's independent chart approval ledger from genuine human review marks.

Reads verified human review marks from docs/reports/2026-11-15_chart_review_inputs.json,
binds each decision to the candidate case SHA-256 fingerprint, validates via
load_reviewed_set, and triggers promotional evaluation gating.
"""

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.charts.dataset import case_fingerprint, load_candidate_set, load_reviewed_set, sha  # noqa: E402


def load_review_marks(inputs_path: Path) -> dict[str, dict]:
    """Load per-case review decisions and visual check notes from JSON."""
    if not inputs_path.is_file():
        raise FileNotFoundError(f"Review marks input file missing: {inputs_path}")

    data = json.loads(inputs_path.read_text(encoding="utf-8"))
    cases_list = data.get("cases", [])
    if not cases_list:
        raise ValueError(f"No cases found in review inputs: {inputs_path}")

    return {c["id"]: c for c in cases_list}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--inputs",
        type=Path,
        default=ROOT / "docs/reports/2026-11-15_chart_review_inputs.json",
        help="Path to per-case review marks JSON file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "docs/reports/2026-11-15_chart_approvals_ujjwal.json",
        help="Path to output approval ledger JSON.",
    )
    args = parser.parse_args()

    charts_dir = ROOT / "data/charts"
    cases, manifest, audit = load_candidate_set(charts_dir)
    print(f"Loaded {len(cases)} candidate chart cases")

    review_marks = load_review_marks(args.inputs)
    print(f"Loaded {len(review_marks)} review marks from {args.inputs}")

    decisions = []
    passed_cases = []
    rejected_cases = []
    unreviewed_cases = []

    for c in cases:
        cid = c["id"]
        if cid not in review_marks:
            unreviewed_cases.append(cid)
            decisions.append({
                "id": cid,
                "case_sha256": case_fingerprint(c),
                "decision": "unreviewed",
                "original_image_checked": False,
                "source_provenance_checked": False,
                "basis": "Unreviewed case - awaiting verification.",
            })
            continue

        mark = review_marks[cid]
        decision = mark.get("decision", "passed")
        orig_checked = mark.get("original_image_checked", False)
        prov_checked = mark.get("source_provenance_checked", False)
        basis = mark.get("reviewer_notes") or mark.get("basis", "")

        if decision == "passed" and orig_checked and prov_checked:
            passed_cases.append(cid)
        elif decision == "rejected":
            rejected_cases.append(cid)
        else:
            unreviewed_cases.append(cid)

        decisions.append({
            "id": cid,
            "case_sha256": case_fingerprint(c),
            "decision": decision,
            "original_image_checked": orig_checked,
            "source_provenance_checked": prov_checked,
            "basis": basis,
        })

    total_count = len(cases)
    passed_count = len(passed_cases)
    all_passed_and_checked = (passed_count == total_count) and not rejected_cases and not unreviewed_cases

    # Use human method only if all cases were inspected against original image & source
    method = "human_original_image_and_source" if all_passed_and_checked else "ai_assisted_unreviewed"

    ledger = {
        "schema_version": 1,
        "candidate_binding": {
            "question_set_sha256": sha((charts_dir / "question-set.json").read_bytes()),
            "question_files_sha256": audit["question_files_sha256"],
            "source_manifest_sha256": audit["source_manifest_sha256"],
        },
        "reviewer_identity": "Ujjwal Chandak",
        "reviewed_at": datetime.now(UTC).isoformat(),
        "method": method,
        "review_summary": {
            "total_candidates": total_count,
            "passed": passed_count,
            "rejected": len(rejected_cases),
            "unreviewed": len(unreviewed_cases),
            "shortfall": total_count - passed_count,
        },
        "decisions": decisions,
    }

    if rejected_cases:
        print(f"\n[ALERT] Rejection shortfall: {passed_count}/{total_count} passed.")
        print(f"Tell author (Rushil Mohan) to address {len(rejected_cases)} rejected cases:")
        for r_id in rejected_cases:
            print(f"  - {r_id}")
    elif unreviewed_cases:
        print(f"\n[WARNING] Incomplete review shortfall: {passed_count}/{total_count} passed. Unreviewed: {len(unreviewed_cases)}")
    else:
        print(f"\n[SUCCESS] All {total_count}/{total_count} candidate chart questions verified and passed!")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
    print(f"Wrote ledger to {args.output}")

    # Validate ledger via load_reviewed_set
    try:
        reviewed, _, report = load_reviewed_set(
            charts_dir,
            args.output,
            trusted_reviewers={"Ujjwal Chandak"},
            label_authors={"Rushil Mohan", "rmo29", "ai-assisted"},
        )
        print("load_reviewed_set validation passed successfully!")
        print(f"Status: {report['status']}, evaluation_ready: {report['evaluation_ready']}")
    except ValueError as exc:
        print(f"load_reviewed_set noted non-human or incomplete approval: {exc}")


if __name__ == "__main__":
    main()
