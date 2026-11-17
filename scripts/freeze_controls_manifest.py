"""Prepare a DRAFT control manifest; automation cannot invent human acceptance or freeze."""
import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.benchmark.gates import evaluate_gates  # noqa: E402
from src.benchmark.inventory import build_inventory, digest  # noqa: E402
from src.pipeline.experiment_scaffold import FROZEN_CONTROLS, VARIANT_SPECS  # noqa: E402


def prepare_draft(directory):
    inventory = build_inventory(directory, ROOT / "data/charts")
    gates = evaluate_gates()
    return {
        "schema_version": 2, "purpose": "draft_experimental_controls_manifest",
        "status": "draft_not_frozen", "prepared_by": "automated_artifact_inventory",
        "prepared_at": datetime.now(UTC).isoformat(), "frozen_by": None, "frozen_at": None,
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "common_controls": dict(FROZEN_CONTROLS), "benchmark_data": inventory,
        "model_profiles": {name: {"path": str(path.relative_to(ROOT)), "sha256": digest(path)}
                           for name, path in (("primary", ROOT / "configs/gemma3-4b.json"),
                                              ("comparison", ROOT / "configs/llama32-comparison.json"))},
        "prompt_template_sha256": digest(ROOT / "src/llm/prompts.py"),
        "variants": {key: spec.to_dict() for key, spec in VARIANT_SPECS.items()},
        "prerequisite_gate_status": gates,
        "execution_parameters": {"max_context_passages": 5, "context_token_budget": None,
                                 "tokenizer_identity": None, "route_thresholds": "unfrozen"},
        "capacity_gate_decision": {"status": "unmeasured", "approved_by": None,
                                   "estimated_hours": None, "measured_machine": None},
        "missing_freeze_evidence": ["independent acceptance", "source-equivalent executable variants",
                                    "pinned actual tokenizer and effective token budget", "development-only routing calibration",
                                    "representative capacity pilot", "predeclared independent output sample"],
        "final_experiment_ready": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "output/benchmarks/draft_controls.json")
    args = parser.parse_args()
    document = prepare_draft(args.benchmark_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, indent=2) + "\n")
    print("Draft controls saved. No human approval, measured capacity or final freeze was created.")


if __name__ == "__main__":
    main()
