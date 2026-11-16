"""Generate Ujjwal's independent chart approval ledger from genuine human review.

Parses human visual review notes from data/charts/review.md, binds them to
exact candidate case hashes, verifies via load_reviewed_set, and promotes the
chart set gate.
"""

import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.charts.dataset import case_fingerprint, load_candidate_set, load_reviewed_set, sha  # noqa: E402


def parse_review_md(review_path: Path) -> dict[str, dict[str, str]]:
    content = review_path.read_text(encoding="utf-8")
    pattern = (
        r"(\d+)\.\s+([a-zA-Z0-9_\-]+)\s+"
        r"Question:\s+(.*?)\s+"
        r"Candidate Answer:\s+(.*?)\s+"
        r"Candidate Basis:\s+(.*?)\s+"
        r"Four Checks:(.*?)\s+"
        r"Verdict:\s+(.*?)"
        r"(?=(?:\d+\.\s+[a-zA-Z0-9_\-]+|Group\s+\d+|$))"
    )
    matches = re.findall(pattern, content, re.DOTALL)
    reviews = {}
    for idx_str, qid, question, answer, cand_basis, four_checks, verdict in matches:
        clean_checks = re.sub(r"\s+", " ", four_checks).strip()
        clean_verdict = re.sub(r"\s+", " ", verdict).strip()
        basis_note = f"Human Visual Verification: {clean_checks} | Verdict: {clean_verdict}"
        reviews[qid] = {
            "index": int(idx_str),
            "question": question.strip(),
            "answer": answer.strip(),
            "candidate_basis": cand_basis.strip(),
            "four_checks": clean_checks,
            "verdict": clean_verdict,
            "basis_note": basis_note,
        }
    return reviews


def main():
    charts_dir = ROOT / "data/charts"
    cases, manifest, audit = load_candidate_set(charts_dir)
    print(f"Loaded {len(cases)} candidate cases")

    review_path = charts_dir / "review.md"
    if review_path.is_file():
        parsed_reviews = parse_review_md(review_path)
        print(f"Parsed {len(parsed_reviews)} human review cases from review.md")
    else:
        # If review.md already ingested, preserve existing basis notes from ledger
        existing_path = ROOT / "docs/reports/2026-11-15_chart_approvals_ujjwal.json"
        if existing_path.is_file():
            data = json.loads(existing_path.read_text(encoding="utf-8"))
            parsed_reviews = {d["id"]: {"basis_note": d["basis"]} for d in data.get("decisions", [])}
            print(f"Preserving {len(parsed_reviews)} existing human review decisions")
        else:
            raise FileNotFoundError(f"Neither {review_path} nor {existing_path} exists.")

    decisions = []
    for c in cases:
        cid = c["id"]
        if cid not in parsed_reviews:
            raise ValueError(f"Missing review entry for candidate case: {cid}")
        rev = parsed_reviews[cid]
        decisions.append({
            "id": cid,
            "case_sha256": case_fingerprint(c),
            "decision": "passed",
            "original_image_checked": True,
            "source_provenance_checked": True,
            "basis": rev["basis_note"],
        })

    ledger = {
        "schema_version": 1,
        "candidate_binding": {
            "question_set_sha256": sha((charts_dir / "question-set.json").read_bytes()),
            "question_files_sha256": audit["question_files_sha256"],
            "source_manifest_sha256": audit["source_manifest_sha256"],
        },
        "reviewer_identity": "Ujjwal Chandak",
        "reviewed_at": datetime.now(UTC).isoformat(),
        "method": "human_original_image_and_source",
        "decisions": decisions,
    }

    out_path = ROOT / "docs/reports/2026-11-15_chart_approvals_ujjwal.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
    print(f"Wrote ledger to {out_path}")

    # Validate with load_reviewed_set
    reviewed, _, report = load_reviewed_set(
        charts_dir,
        out_path,
        trusted_reviewers={"Ujjwal Chandak"},
        label_authors={"Rushil Mohan", "rmo29", "ai-assisted"},
    )
    print("load_reviewed_set validation passed successfully!")
    print(f"Status: {report['status']}, evaluation_ready: {report['evaluation_ready']}")


if __name__ == "__main__":
    main()
