"""Freeze experimental controls, code revisions, model configurations, and case pools (Ujjwal Nov 15)."""

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.charts.dataset import sha  # noqa: E402
from src.pipeline.experiment_scaffold import CANONICAL_VARIANTS, FROZEN_CONTROLS, get_variant_spec  # noqa: E402


def get_git_revision() -> str:
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
        return out
    except Exception:
        return "unknown"


def main():
    git_rev = get_git_revision()

    # Model configuration digests
    gemma_cfg = ROOT / "configs/gemma3-4b.json"
    gemma_digest = sha(gemma_cfg.read_bytes()) if gemma_cfg.is_file() else None

    llama_cfg = ROOT / "configs/llama32-comparison.json"
    llama_digest = sha(llama_cfg.read_bytes()) if llama_cfg.is_file() else None

    # Benchmark dataset files and digests
    fb_path = ROOT / "data/benchmarks/financebench_open150.json"
    finqa_path = ROOT / "data/benchmarks/finqa_candidate_universe.json"
    tatqa_path = ROOT / "data/benchmarks/tatqa_candidate_universe.json"
    charts_manifest = ROOT / "data/charts/chart-sources.json"

    benchmark_manifest = {
        "FinanceBench_Open150": {
            "path": "data/benchmarks/financebench_open150.json",
            "sha256": sha(fb_path.read_bytes()) if fb_path.is_file() else None,
            "case_count": 150,
        },
        "FinQA_Candidate": {
            "path": "data/benchmarks/finqa_candidate_universe.json",
            "sha256": sha(finqa_path.read_bytes()) if finqa_path.is_file() else None,
            "case_count": 50,
        },
        "TAT-QA_Candidate": {
            "path": "data/benchmarks/tatqa_candidate_universe.json",
            "sha256": sha(tatqa_path.read_bytes()) if tatqa_path.is_file() else None,
            "case_count": 50,
        },
        "Charts_Dev_Heldout": {
            "path": "data/charts/chart-sources.json",
            "sha256": sha(charts_manifest.read_bytes()) if charts_manifest.is_file() else None,
            "case_count": 50,
        },
    }

    # Variant specifications and gate statuses
    variant_manifest = {}
    for vid in CANONICAL_VARIANTS:
        spec = get_variant_spec(vid)
        variant_manifest[vid] = {
            "name": spec.name,
            "description": spec.description,
            "narrative_rep": spec.narrative_representation,
            "table_rep": spec.table_representation,
            "retrieval_mode": spec.retrieval_mode,
            "chart_tier_enabled": spec.chart_tier_enabled,
            "prerequisite_gates": list(spec.prerequisite_gates),
            "status": "ready" if not spec.prerequisite_gates else "gated",
        }

    manifest = {
        "schema_version": 1,
        "purpose": "frozen_experimental_controls_and_execution_manifest",
        "frozen_by": "Ujjwal Chandak",
        "frozen_at": datetime.now(UTC).isoformat(),
        "git_commit": git_rev,
        "common_controls": dict(FROZEN_CONTROLS),
        "execution_parameters": {
            "max_context_passages": 5,
            "context_token_budget": 4000,
            "numerical_relative_tolerance": 0.01,
            "zero_absolute_tolerance": 0.001,
            "random_seed": 42,
            "calculator_mode": "restricted_decimal_trees_fail_closed",
            "checkpoint_schema": "atomic_append_jsonl_with_run_manifest",
        },
        "model_profiles": {
            "primary": {
                "tag": "gemma3:4b",
                "config_path": "configs/gemma3-4b.json",
                "config_sha256": gemma_digest,
                "pinned_digest": FROZEN_CONTROLS["generator_digest"],
            },
            "comparison": {
                "tag": "llama3.2:3b",
                "config_path": "configs/llama32-comparison.json",
                "config_sha256": llama_digest,
            },
        },
        "benchmark_data": benchmark_manifest,
        "variants": variant_manifest,
        "capacity_gate_decision": {
            "measured_machine": "12 cores Intel x86_64, 15.7 GB RAM",
            "full_cpu_estimate_hours": 90.87,
            "deadline_window_hours": 72.0,
            "status": "core_suite_prioritized",
            "approved_prioritized_cases": 300,
            "approved_estimated_hours": 9.05,
        },
        "prerequisite_gate_status": {
            "canonical_cells_and_parents": "available_via_corpus_audit",
            "fixed_overlap_index_representation": "available_via_corpus_audit",
            "section_aware_index_representation": "available_via_corpus_audit",
            "independent_chart_approval": "gated_ai_assisted_review_only",
            "bge_reranker_base": "gated_unfitted",
            "frozen_routing_thresholds": "gated_uncalibrated",
        },
    }

    out_path = ROOT / "docs/reports/2026-11-15_frozen_manifest.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote frozen controls manifest to {out_path}")


if __name__ == "__main__":
    main()
