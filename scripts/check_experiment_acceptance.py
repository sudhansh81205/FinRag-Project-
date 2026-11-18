"""Exercise all available suite/variant acceptance paths without fabricating runs.

Exit2 means manual acceptance or an execution dependency remains blocked. No
model calls, gold-prompt leakage, reviewer signatures or approvals are generated.
"""
import argparse
import json
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.benchmark.gates import detect_available_gates, evaluate_gates  # noqa: E402
from src.benchmark.runner import BenchmarkRunner  # noqa: E402
from src.charts.dataset import load_candidate_set  # noqa: E402


def check(benchmark_dir, output):
    gates = detect_available_gates()
    rows = []
    files = {"FinanceBench": "financebench_open150.json", "FinQA": "finqa_candidate_universe.json", "TAT-QA": "tatqa_candidate_universe.json"}
    with tempfile.TemporaryDirectory(prefix="finrag-acceptance-") as temporary:
        for variant in "ABCDEFG":
            for suite, filename in files.items():
                runner = BenchmarkRunner(Path(temporary) / variant / suite, variant=variant, benchmark=suite,
                                         available_gates=gates, data_path=benchmark_dir / filename)
                # An absent independent gate must be tested before an engine is loaded.
                result = runner.run(max_cases=0)
                rows.append({k: result.get(k) for k in ("variant", "benchmark", "status", "eligible_cases", "attempted_outputs", "missing_gates", "context_binding", "message")})
    cases, _, chart_audit = load_candidate_set(ROOT / "data/charts")
    for variant in "ABCDEFG":
        rows.append({"variant": variant, "benchmark": "Chart", "status": "blocked_independent_review",
                     "eligible_candidates": len(cases), "attempted_outputs": 0,
                     "reason": "Independent source/caption decisions, final common controls and chart-suite execution are not accepted. Candidate inspection is not a final run."})
    result = {"checked_at_utc": datetime.now(UTC).isoformat(), "purpose": "acceptance preflight, not model execution or benchmark scores",
              "matrix_cells_checked": len(rows), "final_matrix_cells_completed": 0,
              "gates": evaluate_gates(), "matrix": rows, "chart_integrity": chart_audit,
              "technical_dependencies": ["A source-equivalent canonical benchmark adapter remains absent: current runner reports UNBOUND.",
                  "Chart-suite final execution, RAGAS evaluator and separate Llama comparison are not completed.",
                  "Full source mapping, typed benchmark periods/units, development capacity measurement and immutable accepted freeze must precede final runs."],
              "manual_dependencies": ["Real independent original-source and chart-question/caption review", "Hash-bound acceptance by an actual eligible person", "Predeclared separate fifty-output audit after complete generated outputs"]}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"matrix_cells_checked": len(rows), "attempted_model_outputs": 0, "final_matrix_completed": 0,
                      "status": "blocked", "open_gates": sorted(gates), "output": str(output)}, indent=2))
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--benchmark-dir", type=Path, default=ROOT / "output/benchmarks/official")
    p.add_argument("--output", type=Path, default=ROOT / "output/final-checks/experiment-acceptance.json")
    a = p.parse_args()
    check(a.benchmark_dir, a.output)
    raise SystemExit(2)
