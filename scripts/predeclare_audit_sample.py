"""Predeclare the seeded stratified 50-output faithfulness audit sample (Ujjwal Nov 15)."""

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.benchmark.loaders import (  # noqa: E402
    load_financebench_open150,
    load_finqa,
    load_tatqa,
)
from src.charts.dataset import load_candidate_set  # noqa: E402
from src.pipeline.experiment_scaffold import FROZEN_CONTROLS  # noqa: E402


def main():
    # Seed must be strictly frozen
    seed = FROZEN_CONTROLS["random_seed"]
    random.seed(seed)

    # Load candidate universe cases (each loader returns list of (BenchmarkCase, GoldReference))
    fb_pairs = load_financebench_open150()
    finqa_pairs = load_finqa()
    tatqa_pairs = load_tatqa()
    chart_cases, _, _ = load_candidate_set(ROOT / "data/charts")

    print(f"Loaded benchmark pools: FB={len(fb_pairs)}, FinQA={len(finqa_pairs)}, TAT-QA={len(tatqa_pairs)}, Charts={len(chart_cases)}")

    # Stratification strategy: 50 cases total across 7 variants (A-G)
    variant_quotas = {
        "A": 7,
        "B": 7,
        "C": 7,
        "D": 7,
        "E": 7,
        "F": 7,
        "G": 8,
    }

    sampled_audit_cases = []
    audit_idx = 1

    for variant, quota in variant_quotas.items():
        if variant == "G":
            # Variant G prioritizes chart-enabled questions and multimodal checks
            pool = chart_cases
            selected = random.sample(pool, min(quota, len(pool)))
            for case in selected:
                sampled_audit_cases.append({
                    "audit_id": f"AUDIT-{audit_idx:02d}",
                    "variant": variant,
                    "benchmark": "Charts_Dev_Heldout",
                    "case_id": case["id"],
                    "question_text": case["question"],
                    "question_type": "chart_multimodal",
                    "expected_reviewer": "Agrawal Pavan Shailesh (Pavan)",
                    "label_author": "B Rushil Mohan (Rushil) / AI-assisted",
                    "authorship_conflict": False,
                    "review_scheduled_date": "2026-11-16",
                })
                audit_idx += 1
        else:
            # Distribute across FinanceBench (3), FinQA (2), TAT-QA (2) for total 7
            fb_sample = random.sample(fb_pairs, 3)
            finqa_sample = random.sample(finqa_pairs, 2)
            tatqa_sample = random.sample(tatqa_pairs, 2)

            for case, _ in fb_sample:
                sampled_audit_cases.append({
                    "audit_id": f"AUDIT-{audit_idx:02d}",
                    "variant": variant,
                    "benchmark": "FinanceBench_Open150",
                    "case_id": case.case_id,
                    "question_text": case.question,
                    "question_type": case.question_type or "narrative_numerical",
                    "expected_reviewer": "Agrawal Pavan Shailesh (Pavan)",
                    "label_author": "FinanceBench Official",
                    "authorship_conflict": False,
                    "review_scheduled_date": "2026-11-16",
                })
                audit_idx += 1

            for case, _ in finqa_sample:
                sampled_audit_cases.append({
                    "audit_id": f"AUDIT-{audit_idx:02d}",
                    "variant": variant,
                    "benchmark": "FinQA_Candidate",
                    "case_id": case.case_id,
                    "question_text": case.question,
                    "question_type": case.question_type or "arithmetic_reasoning",
                    "expected_reviewer": "Agrawal Pavan Shailesh (Pavan)",
                    "label_author": "FinQA Official",
                    "authorship_conflict": False,
                    "review_scheduled_date": "2026-11-16",
                })
                audit_idx += 1

            for case, _ in tatqa_sample:
                sampled_audit_cases.append({
                    "audit_id": f"AUDIT-{audit_idx:02d}",
                    "variant": variant,
                    "benchmark": "TAT-QA_Candidate",
                    "case_id": case.case_id,
                    "question_text": case.question,
                    "question_type": case.question_type or "hybrid_table_text",
                    "expected_reviewer": "Agrawal Pavan Shailesh (Pavan)",
                    "label_author": "TAT-QA Official",
                    "authorship_conflict": False,
                    "review_scheduled_date": "2026-11-16",
                })
                audit_idx += 1

    assert len(sampled_audit_cases) == 50, f"Expected exactly 50 cases, got {len(sampled_audit_cases)}"

    predeclaration = {
        "schema_version": 1,
        "purpose": "predeclared_seeded_stratified_output_faithfulness_sample",
        "auditor_predeclaring": "Ujjwal Chandak",
        "predeclared_at": "2026-11-15T18:40:00+05:30",
        "random_seed": seed,
        "total_sample_count": 50,
        "strata_distribution": {
            "A": 7, "B": 7, "C": 7, "D": 7, "E": 7, "F": 7, "G": 8
        },
        "benchmark_distribution": {
            "FinanceBench_Open150": 18,
            "FinQA_Candidate": 12,
            "TAT-QA_Candidate": 12,
            "Charts_Dev_Heldout": 8
        },
        "reviewer_assignment_summary": {
            "primary_reviewer": "Agrawal Pavan Shailesh (Nov 16)",
            "conflict_escalation_reviewer": "Sudhansh Khandelwal (Nov 17)",
            "conflict_count": 0,
            "independent_review_guaranteed": True
        },
        "audit_sampling_rule": (
            "Stratified across variants A-G and representative question types. "
            "Predeclared before inspecting output scores or accuracy to eliminate selection bias."
        ),
        "cases": sampled_audit_cases,
    }

    out_path = ROOT / "docs/reports/2026-11-15_audit_sampling_predeclaration.json"
    out_path.write_text(json.dumps(predeclaration, indent=2), encoding="utf-8")
    print(f"Predeclared exactly {len(sampled_audit_cases)} stratified cases to {out_path}")


if __name__ == "__main__":
    main()
