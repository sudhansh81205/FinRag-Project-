"""Run or resume FinRAG benchmarks with immutable controls and gate checks.

Usage:
  python scripts/run_benchmarks.py --variant D --benchmark FinanceBench --max-cases 10
  python scripts/run_benchmarks.py --profile-capacity
"""

import argparse
import json
import sys
from pathlib import Path

# Ensure repository root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.benchmark.capacity import measure_machine_capacity  # noqa: E402
from src.benchmark.runner import BenchmarkRunner  # noqa: E402


def detect_available_gates() -> set[str]:
    """Auto-detect prerequisite gates verified by independent audit reports."""
    gates = set()
    chart_promo = ROOT / "docs/reports/2026-11-15_chart_promotion_report.json"
    if chart_promo.is_file():
        try:
            data = json.loads(chart_promo.read_text(encoding="utf-8"))
            if data.get("independent_review") == "passed" and data.get("evaluation_ready"):
                gates.add("independent_chart_approval")
        except Exception as exc:
            import logging
            logging.warning("Failed to parse chart promotion report for gate detection: %s", exc)

    corpus_audit = ROOT / "docs/reports/2026-11-15_corpus_audit.json"
    if corpus_audit.is_file():
        try:
            data = json.loads(corpus_audit.read_text(encoding="utf-8"))
            if data.get("status") in ("independently_accepted", "ai_assisted_accepted", "ai_assisted_verified"):
                gates.add("canonical_cells_and_parents")
                gates.add("fixed_overlap_index_representation")
                gates.add("section_aware_index_representation")
        except Exception as exc:
            import logging
            logging.warning("Failed to parse corpus audit report for gate detection: %s", exc)
    return gates


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", default="D", choices=["A", "B", "C", "D", "E", "F", "G"],
                        help="Canonical variant specification to evaluate.")
    parser.add_argument("--benchmark", default="FinanceBench",
                        choices=["FinanceBench", "FinQA", "TAT-QA"],
                        help="Benchmark suite candidate universe.")
    parser.add_argument("--output-dir", default=None,
                        help="Directory to store run manifests and results.jsonl")
    parser.add_argument("--max-cases", type=int, default=None,
                        help="Optional limit on number of cases (e.g. for smoke/pilot runs)")
    parser.add_argument("--model-config", default="configs/gemma3-4b.json",
                        help="Model configuration JSON profile.")
    parser.add_argument("--gate", action="append", dest="available_gates", default=[],
                        help="Declare an available verified prerequisite gate (repeatable)")
    parser.add_argument("--profile-capacity", action="store_true",
                        help="Profile machine hardware and print capacity timeline vs Nov 17.")
    args = parser.parse_args()

    if args.profile_capacity:
        capacity_report = measure_machine_capacity()
        print(json.dumps(capacity_report, indent=2))
        return

    detected_gates = detect_available_gates() | set(args.available_gates)
    out_dir = Path(args.output_dir) if args.output_dir else ROOT / "output" / f"eval_{args.variant}_{args.benchmark.lower()}"
    runner = BenchmarkRunner(
        output_dir=out_dir,
        variant=args.variant,
        benchmark=args.benchmark,
        model_config_path=args.model_config,
        available_gates=detected_gates,
    )

    print(f"Starting or resuming run for Variant {args.variant} on {args.benchmark} (available gates: {sorted(detected_gates)})...")
    summary = runner.run(max_cases=args.max_cases)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
