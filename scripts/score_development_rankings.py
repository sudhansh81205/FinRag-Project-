"""Re-score frozen development retrieval rankings with operand-level nDCG@10."""

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.validation_metrics import clustered_interval  # noqa: E402


def operand_ndcg_at_10(ranking, operand_groups):
    """Discount each required operand's first hit. Equivalent source rows earn gain once."""
    group_by_id = {
        evidence_id: group for group, ids in enumerate(operand_groups) for evidence_id in ids
    }
    if not operand_groups or any(not ids for ids in operand_groups):
        raise ValueError("Every question needs at least one nonempty operand group")
    if len(group_by_id) != sum(len(ids) for ids in operand_groups):
        raise ValueError("Operand groups must contain distinct source IDs")
    if len(ranking) != len(set(ranking)):
        raise ValueError("Ranked evidence IDs must be unique")

    first_hit_ranks = {}
    for rank, evidence_id in enumerate(ranking[:10], start=1):
        if evidence_id in group_by_id:
            first_hit_ranks.setdefault(group_by_id[evidence_id], rank)
    dcg = sum(1 / math.log2(rank + 1) for rank in first_hit_ranks.values())
    ideal_dcg = sum(1 / math.log2(rank + 1) for rank in range(1, min(len(operand_groups), 10) + 1))
    return dcg / ideal_dcg


def score(study):
    hashes = json.loads((study / "artifact-hashes.json").read_text())
    inputs = {}
    for name in ("cases.json", "retrieval-results.json"):
        data = (study / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != hashes[name]:
            raise ValueError(f"Frozen input digest mismatch: {name}")
        inputs[name] = json.loads(data)
    cases = {
        case["id"]: case for case in inputs["cases.json"]
        if case["category"] == "numerical" and case["reference"]["expected_status"] == "ok"
    }
    rankings = inputs["retrieval-results.json"]["rows"]
    if len(rankings) != len(cases) or {row["id"] for row in rankings} != cases.keys():
        raise ValueError("Rankings must cover each labelled case exactly once")
    rows = []
    for row in rankings:
        case = cases[row["id"]]
        if case["accession"] != row["accession"]:
            raise ValueError(f"Filing accession mismatch: {row['id']}")
        groups = case["reference"]["operand_groups"]
        dense = operand_ndcg_at_10(row["dense_ids"], groups)
        hybrid = operand_ndcg_at_10(row["hybrid_ids"], groups)
        rows.append({"id": row["id"], "accession": row["accession"], "dense": dense,
                     "hybrid": hybrid, "paired_delta": hybrid - dense})
    return {
        "metric": "Operand nDCG@10",
        "scope": "Supplemental re-scoring of original question rankings on FinRAG development data",
        "case_count": len(rows),
        "input_sha256": {name: hashes[name] for name in inputs},
        "summary": {key: clustered_interval(rows, key) for key in ("dense", "hybrid", "paired_delta")},
        "rows": rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", type=Path, default=ROOT / "docs/validation/2026-11-18-results")
    args = parser.parse_args()
    print(json.dumps(score(args.study), indent=2))


if __name__ == "__main__":
    main()
