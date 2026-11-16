"""Freeze experimental controls, code revisions, model configurations, and case pools (Ujjwal Nov 15/16)."""

import hashlib
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


def sha256_list(items: list[str]) -> str:
    """Compute deterministic SHA-256 fingerprint over sorted list of strings."""
    canonical = json.dumps(sorted(items), separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def main():
    git_rev = get_git_revision()

    # Model configuration digests
    gemma_cfg = ROOT / "configs/gemma3-4b.json"
    gemma_digest = sha(gemma_cfg.read_bytes()) if gemma_cfg.is_file() else None

    llama_cfg = ROOT / "configs/llama32-comparison.json"
    llama_digest = sha(llama_cfg.read_bytes()) if llama_cfg.is_file() else None

    # Prompt template hash
    prompts_file = ROOT / "src/llm/prompts.py"
    prompt_template_sha256 = sha(prompts_file.read_bytes()) if prompts_file.is_file() else None

    # Benchmark dataset files and dynamic case counts / ID hashes
    fb_path = ROOT / "data/benchmarks/financebench_open150.json"
    fb_cases = json.loads(fb_path.read_text(encoding="utf-8")) if fb_path.is_file() else []
    fb_ids = [c["case_id"] for c in fb_cases]

    finqa_path = ROOT / "data/benchmarks/finqa_candidate_universe.json"
    finqa_cases = json.loads(finqa_path.read_text(encoding="utf-8")) if finqa_path.is_file() else []
    finqa_ids = [c["case_id"] for c in finqa_cases]

    tatqa_path = ROOT / "data/benchmarks/tatqa_candidate_universe.json"
    tatqa_cases = json.loads(tatqa_path.read_text(encoding="utf-8")) if tatqa_path.is_file() else []
    tatqa_ids = [c["case_id"] for c in tatqa_cases]

    charts_manifest = ROOT / "data/charts/chart-sources.json"
    c_dev_path = ROOT / "data/charts/apple-2021-candidate-questions.json"
    c_held_path = ROOT / "data/charts/heldout-35-candidate-questions.json"
    c_dev_cases = json.loads(c_dev_path.read_text(encoding="utf-8")) if c_dev_path.is_file() else []
    c_held_cases = json.loads(c_held_path.read_text(encoding="utf-8")) if c_held_path.is_file() else []
    charts_all_ids = [c["id"] for c in c_dev_cases] + [c["id"] for c in c_held_cases]

    benchmark_manifest = {
        "FinanceBench_Open150": {
            "path": "data/benchmarks/financebench_open150.json",
            "sha256": sha(fb_path.read_bytes()) if fb_path.is_file() else None,
            "case_count": len(fb_ids),
            "case_ids_sha256": sha256_list(fb_ids),
            "is_subset": False,
        },
        "FinQA_Candidate": {
            "path": "data/benchmarks/finqa_candidate_universe.json",
            "sha256": sha(finqa_path.read_bytes()) if finqa_path.is_file() else None,
            "case_count": len(finqa_ids),
            "case_ids_sha256": sha256_list(finqa_ids),
            "is_subset": True,
        },
        "TAT-QA_Candidate": {
            "path": "data/benchmarks/tatqa_candidate_universe.json",
            "sha256": sha(tatqa_path.read_bytes()) if tatqa_path.is_file() else None,
            "case_count": len(tatqa_ids),
            "case_ids_sha256": sha256_list(tatqa_ids),
            "is_subset": True,
        },
        "Charts_Dev_Heldout": {
            "path": "data/charts/chart-sources.json",
            "sha256": sha(charts_manifest.read_bytes()) if charts_manifest.is_file() else None,
            "case_count": len(charts_all_ids),
            "case_ids_sha256": sha256_list(charts_all_ids),
            "is_subset": False,
            "dev_case_count": len(c_dev_cases),
            "heldout_case_count": len(c_held_cases),
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

    chart_promo_path = ROOT / "docs/reports/2026-11-15_chart_promotion_report.json"
    chart_gate_cleared = False
    if chart_promo_path.is_file():
        try:
            cp_data = json.loads(chart_promo_path.read_text(encoding="utf-8"))
            chart_gate_cleared = cp_data.get("independent_review") == "passed" and cp_data.get("evaluation_ready")
        except Exception:
            pass

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
            "prompt_template_sha256": prompt_template_sha256,
            "route_thresholds": "unfrozen",
        },
        "model_profiles": {
            "primary": {
                "tag": "gemma3:4b",
                "config_path": "configs/gemma3-4b.json",
                "config_sha256": gemma_digest,
                "pinned_digest": FROZEN_CONTROLS["generator_digest"],
                "prompt_template_sha256": prompt_template_sha256,
            },
            "comparison": {
                "tag": "llama3.2:3b",
                "config_path": "configs/llama32-comparison.json",
                "config_sha256": llama_digest,
                "prompt_template_sha256": prompt_template_sha256,
            },
        },
        "benchmark_data": benchmark_manifest,
        "variants": variant_manifest,
        "capacity_gate_decision": {
            "measured_machine": "12 cores Intel x86_64, 15.7 GB RAM",
            "full_cpu_estimate_hours": 90.87,
            "deadline_window_hours": 72.0,
            "status": "core_suite_prioritized",
            "approved_prioritized_cases": sum(b["case_count"] for b in benchmark_manifest.values()),
            "approved_estimated_hours": 9.05,
        },
        "prerequisite_gate_status": {
            "canonical_cells_and_parents": "available_via_corpus_audit",
            "fixed_overlap_index_representation": "available_via_corpus_audit",
            "section_aware_index_representation": "available_via_corpus_audit",
            "independent_chart_approval": "available_via_independent_review" if chart_gate_cleared else "gated",
            "bge_reranker_base": "gated_unfitted",
            "frozen_routing_thresholds": "unfrozen_uncalibrated",
        },
    }

    out_path = ROOT / "docs/reports/2026-11-15_frozen_manifest.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote frozen controls manifest to {out_path}")


if __name__ == "__main__":
    main()
