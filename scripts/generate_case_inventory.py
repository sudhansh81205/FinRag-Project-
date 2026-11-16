"""Generate formal case inventory across all evaluation benchmarks (PRD Section 4).

Records exact case IDs, splits (dev vs heldout/test), subset designations,
case-ID SHA-256 hashes, and documented exclusions with reasons.
"""

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def sha256_list(items: list[str]) -> str:
    """Compute deterministic SHA-256 fingerprint over sorted list of strings."""
    canonical = json.dumps(sorted(items), separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def main():
    benchmarks_dir = ROOT / "data/benchmarks"
    charts_dir = ROOT / "data/charts"

    # 1. FinanceBench Open 150
    fb_path = benchmarks_dir / "financebench_open150.json"
    fb_data = json.loads(fb_path.read_text(encoding="utf-8"))
    fb_ids = [c["case_id"] for c in fb_data]

    # 2. FinQA Candidate Subset (50 cases)
    fq_path = benchmarks_dir / "finqa_candidate_universe.json"
    fq_data = json.loads(fq_path.read_text(encoding="utf-8"))
    fq_ids = [c["case_id"] for c in fq_data]

    # 3. TAT-QA Candidate Subset (50 cases)
    tq_path = benchmarks_dir / "tatqa_candidate_universe.json"
    tq_data = json.loads(tq_path.read_text(encoding="utf-8"))
    tq_ids = [c["case_id"] for c in tq_data]

    # 4. Charts Dev + Heldout (50 cases: 15 dev / 35 heldout)
    c_dev_path = charts_dir / "apple-2021-candidate-questions.json"
    c_held_path = charts_dir / "heldout-35-candidate-questions.json"
    c_dev_data = json.loads(c_dev_path.read_text(encoding="utf-8"))
    c_held_data = json.loads(c_held_path.read_text(encoding="utf-8"))
    c_dev_ids = [c["id"] for c in c_dev_data]
    c_held_ids = [c["id"] for c in c_held_data]
    c_all_ids = c_dev_ids + c_held_ids

    inventory = {
        "schema_version": 1,
        "purpose": "benchmark_case_and_exclusion_inventory",
        "created_at": datetime.now(UTC).isoformat(),
        "total_prioritized_cases": len(fb_ids) + len(fq_ids) + len(tq_ids) + len(c_all_ids),
        "benchmarks": {
            "FinanceBench_Open150": {
                "name": "FinanceBench Open 150",
                "path": str(fb_path.relative_to(ROOT)).replace("\\", "/"),
                "file_sha256": hashlib.sha256(fb_path.read_bytes()).hexdigest(),
                "total_cases": len(fb_ids),
                "is_subset": False,
                "split": {"open_test": len(fb_ids)},
                "case_ids_sha256": sha256_list(fb_ids),
                "case_ids": fb_ids,
                "exclusions": [
                    {
                        "scope": "financebench_closed_cases",
                        "reason": "proprietary_gold_labels_unreleased",
                        "description": "Closed FinanceBench cases omitted in favor of the standardized Open 150 release.",
                    }
                ],
            },
            "FinQA_Candidate_Universe": {
                "name": "FinQA Candidate Universe",
                "path": str(fq_path.relative_to(ROOT)).replace("\\", "/"),
                "file_sha256": hashlib.sha256(fq_path.read_bytes()).hexdigest(),
                "total_cases": len(fq_ids),
                "is_subset": True,
                "subset_rationale": "PRD requires bounded candidate subset aligned with 18-filing SEC technology corpus.",
                "split": {"test_subset": len(fq_ids)},
                "case_ids_sha256": sha256_list(fq_ids),
                "case_ids": fq_ids,
                "exclusions": [
                    {
                        "scope": "non_corpus_issuers",
                        "reason": "filing_outside_18_filing_corpus",
                        "description": "Full FinQA questions targeting companies outside the 10 technology companies in the corpus.",
                    },
                    {
                        "scope": "non_groundable_tables",
                        "reason": "table_format_incompatible_with_html_extraction",
                        "description": "Cases requiring PDF vector rasterization or missing primary HTML filing tables.",
                    },
                ],
            },
            "TAT-QA_Candidate_Universe": {
                "name": "TAT-QA Candidate Universe",
                "path": str(tq_path.relative_to(ROOT)).replace("\\", "/"),
                "file_sha256": hashlib.sha256(tq_path.read_bytes()).hexdigest(),
                "total_cases": len(tq_ids),
                "is_subset": True,
                "subset_rationale": "PRD requires bounded candidate subset representing hybrid narrative-tabular financial reasoning.",
                "split": {"test_subset": len(tq_ids)},
                "case_ids_sha256": sha256_list(tq_ids),
                "case_ids": tq_ids,
                "exclusions": [
                    {
                        "scope": "non_corpus_annual_reports",
                        "reason": "filing_outside_18_filing_corpus",
                        "description": "Full TAT-QA cases referencing foreign financial statements or non-corpus entities.",
                    },
                    {
                        "scope": "text_only_questions",
                        "reason": "lacks_hybrid_table_requirement",
                        "description": "Questions that do not require joint cross-cell arithmetic and textual extraction.",
                    },
                ],
            },
            "Charts_Performance_Graph": {
                "name": "Charts Performance Graph Candidate Set",
                "paths": [
                    str(c_dev_path.relative_to(ROOT)).replace("\\", "/"),
                    str(c_held_path.relative_to(ROOT)).replace("\\", "/"),
                ],
                "total_cases": len(c_all_ids),
                "is_subset": False,
                "split": {
                    "dev": len(c_dev_ids),
                    "heldout": len(c_held_ids),
                },
                "split_details": {
                    "dev": {
                        "issuer": "Apple Inc. (0000320193-21-000105)",
                        "count": len(c_dev_ids),
                        "case_ids_sha256": sha256_list(c_dev_ids),
                        "case_ids": c_dev_ids,
                    },
                    "heldout": {
                        "issuers": ["NVIDIA", "AMD", "Intel", "Cisco", "Adobe"],
                        "count": len(c_held_ids),
                        "case_ids_sha256": sha256_list(c_held_ids),
                        "case_ids": c_held_ids,
                    },
                },
                "case_ids_sha256": sha256_list(c_all_ids),
                "case_ids": c_all_ids,
                "exclusions": [
                    {
                        "scope": "non_performance_graphs",
                        "reason": "chart_type_outside_return_comparison_scope",
                        "description": "Bar charts, segment pie charts, and unscaled graphics without 5-year cumulative return curves.",
                    },
                    {
                        "scope": "inferred_unprinted_values",
                        "reason": "visual_hallucination_prevention",
                        "description": "Questions asking for exact unprinted coordinate interpolation are rejected/omitted.",
                    },
                ],
            },
        },
    }

    out_path = ROOT / "docs/reports/2026-11-16_case_inventory.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(inventory, indent=2), encoding="utf-8")
    print(f"Saved complete case inventory to {out_path} ({inventory['total_prioritized_cases']} total cases)")


if __name__ == "__main__":
    main()
