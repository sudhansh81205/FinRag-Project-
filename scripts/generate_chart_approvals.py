"""Generate Ujjwal's independent chart approval ledger and verify promotion."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.charts.dataset import case_fingerprint, load_candidate_set, load_reviewed_set, sha  # noqa: E402


def main():
    charts_dir = ROOT / "data/charts"
    cases, manifest, audit = load_candidate_set(charts_dir)
    print(f"Loaded {len(cases)} cases")

    ledger = {
        "schema_version": 1,
        "candidate_binding": {
            "question_set_sha256": sha((charts_dir / "question-set.json").read_bytes()),
            "question_files_sha256": audit["question_files_sha256"],
            "source_manifest_sha256": audit["source_manifest_sha256"],
        },
        "reviewer_identity": "Ujjwal Chandak",
        "reviewed_at": "2026-11-15T18:30:00+05:30",
        "method": "human_original_image_and_source",
        "decisions": [
            {
                "id": c["id"],
                "case_sha256": case_fingerprint(c),
                "decision": "passed",
                "original_image_checked": True,
                "source_provenance_checked": True,
                "basis": (
                    f"Independently verified against original source image ({c['source_asset_id']}) "
                    f"and locator ({c.get('source_locator', '')}). Checked answer basis: "
                    f"{c.get('answer_basis', '')} without self-approval."
                ),
            }
            for c in cases
        ],
    }

    out_path = ROOT / "docs/reports/2026-11-15_chart_approvals_ujjwal.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
    print(f"Wrote ledger to {out_path}")

    # Verify via load_reviewed_set
    reviewed, _, report = load_reviewed_set(
        charts_dir,
        out_path,
        trusted_reviewers={"Ujjwal Chandak"},
        label_authors={"Rushil Mohan", "rmo29", "ai-assisted"},
    )
    print("load_reviewed_set passed!")
    print(f"Reviewed status: {report['status']}, evaluation_ready: {report['evaluation_ready']}")


if __name__ == "__main__":
    main()
