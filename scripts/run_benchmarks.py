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

from src.benchmark.capacity import load_observed_timings, measure_machine_capacity  # noqa: E402
from src.benchmark.gates import detect_available_gates, evaluate_gates  # noqa: E402
from src.benchmark.runner import BenchmarkRunner  # noqa: E402


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
                        help="Profile hardware; timings stay unknown unless --observed-timings is given.")
    parser.add_argument("--observed-timings", default=None,
                        help="JSON pilot record: cold/warm_generation_sec, retrieval_sec, evaluator_sec, "
                             "pilot_case_ids, measured_at, model_identity.")
    parser.add_argument("--retry-overhead", type=float, default=None,
                        help="Declared retry/failure overhead fraction (e.g. 0.1); omitted -> lower bound.")
    parser.add_argument("--gate-report", action="store_true",
                        help="Print per-gate open/closed status derived from actual artifacts and exit.")
    args = parser.parse_args()

    if args.profile_capacity:
        observed = load_observed_timings(args.observed_timings) if args.observed_timings else None
        print(json.dumps(measure_machine_capacity(observed_timings=observed,
                                                  retry_overhead_fraction=args.retry_overhead), indent=2))
        return

    if args.gate_report:
        print(json.dumps(evaluate_gates(), indent=2))
        return

    # Gate names given with --gate are declarations only; the runner still refuses to run without
    # a validated engine, and open gates come from actual artifacts + acceptance (F34).
    detected_gates = detect_available_gates()
    if set(args.available_gates) - detected_gates:
        parser.error("--gate cannot open an unaccepted prerequisite. Validate the bound artifacts and acceptance record first.")
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
