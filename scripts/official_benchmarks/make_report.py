"""Build a plain-text report from measured local outputs."""

import hashlib
import json
import statistics
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ROOT = REPO / "docs/validation/official-source"
results = ROOT / "results"
lines = [
    "FinRAG official-source evaluation",
    "Measured 18 November 2026",
    "",
    "These runs use the restored official benchmark source pools.",
    "The primary lexical baseline attempted all 2,960 questions.",
    "Tables are ranked as whole tables and FinanceBench at page level.",
    "Labels enter scoring only. Three TAT-QA questions have no mapped",
    "gold evidence IDs, so their retrieval metrics are undefined.",
    "",
    "BM25 retrieval results",
    "",
    "Suite         Attempted   Labelled  Recall@5  Recall@10  MRR@10  nDCG@10",
]
for name in ("FinanceBench", "FinQA", "TAT-QA"):
    report = json.loads((results / name / "summary.json").read_text())
    m = report["metrics"]
    lines.append(
        f"{name:13} {report['attempted']:5}       {report['labelled']:5}     "
        f"{m['recall_at_5']['estimate']:.4f}    {m['recall_at_10']['estimate']:.4f}    "
        f"{m['mrr_at_10']['estimate']:.4f}  {m['ndcg_at_10']['estimate']:.4f}"
    )
lines += [
    "",
    "95% intervals use 10,000 whole-document bootstrap resamples, seed 42.",
    "The per-suite summary JSON retains intervals and case counts.",
    "",
    "BGE dense and BM25/RRF60 comparison",
    "",
]
for name in ("FinanceBench", "FinQA", "TAT-QA"):
    path = results / name / "dense-hybrid-summary.json"
    if not path.exists():
        lines.append(name + ": execution incomplete; check dense-cache checkpoints.")
        continue
    row = json.loads(path.read_text())
    lines.append(name + f": {row['cases']} questions")
    for key in ("recall_at_5", "recall_at_10", "complete_at_10", "mrr_at_10", "ndcg_at_10"):
        m = row["metrics"][key]
        lines.append(
            f"  {key}: dense {m['dense']['estimate']:.4f}, hybrid {m['hybrid']['estimate']:.4f}, "
            f"delta {m['delta']['estimate']:+.4f} [{m['delta']['low']:+.4f}, {m['delta']['high']:+.4f}]"
        )
lines += ["", "Generation pilot", ""]
for name in ("FinanceBench", "FinQA", "TAT-QA"):
    path = results / name / "generation-pilot.json"
    if not path.exists():
        lines.append(name + ": pending execution.")
        continue
    r = json.loads(path.read_text())
    lines += [
        name + ": " + r["result"]["status"] + f" ({r['latency_seconds']:.1f} seconds)",
        "  " + r["case_id"],
        "  " + r["result"].get("text", r["result"].get("error", ""))[:1200],
    ]
timings = [
    json.loads((results / name / "generation-pilot.json").read_text())["latency_seconds"]
    for name in ("FinanceBench", "FinQA", "TAT-QA")
]
mean_seconds = statistics.mean(timings)
answer_runs = 2960 * 7
projected_hours = answer_runs * mean_seconds / 3600
capacity = [
    "Computational budget and evaluation scope",
    "",
    "The full generated-answer benchmark could not be completed within the",
    "time available for this evaluation. We prioritised the complete keyword",
    "retrieval baseline, the FinQA and TAT-QA dense/hybrid comparisons, and",
    "three source-grounded generation pilots to obtain reproducible results.",
    "",
    f"The three Gemma pilots took {timings[0]:.2f}, {timings[1]:.2f} and",
    f"{timings[2]:.2f} seconds, averaging {mean_seconds:.2f} seconds per question.",
    "Applying this observed average to the 2,960 text/table questions across",
    f"the seven A-G variants gives {answer_runs:,} answer-generation requests.",
    f"{answer_runs:,} x {mean_seconds:.2f} / 3,600 = {projected_hours:.1f} machine-hours",
    f"(approximately {projected_hours / 24:.1f} days of continuous sequential execution).",
    "",
    "This preliminary capacity estimate uses one pilot question per dataset.",
    "Actual runtime will vary with context length, variant, model residency,",
    "failures and hardware. The estimate excludes chart processing, RAGAS",
    "judging, the separate Llama comparison, reruns and independent human review.",
    "The 403-hour figure describes projected workload; those hours were not run.",
    "",
    "The completed retrieval results therefore support a bounded evaluation",
    "of evidence ranking. Full A-G answer generation and acceptance remain",
    "future work, together with the remaining representation integration,",
    "evaluator implementation and independent audit.",
    "",
]
lines += [
    "",
    "Pilot observations",
    "",
    "FinanceBench returned 1,888 for capital expenditure; the official reference is",
    "1,577. The cited output used a cost-of-sales value. FinQA refused for",
    "insufficient evidence. TAT-QA returned the expected modified retrospective",
    "method. These are three observed cases; no overall answer-accuracy",
    "estimate is supported by this pilot.",
    "",
    "Execution status",
    "",
    "FinanceBench dense/hybrid was stopped at the user request after 2,304",
    "of 25,950 chunks were checkpointed. No FinanceBench dense score is reported.",
    "",
    *capacity,
    "PRD acceptance",
    "",
    "The benchmark sources are now consumed directly by this isolated adapter.",
    "Each ranking retains original source IDs and has no missing labelled sources.",
    "The cumulative A-G representations, complete generated-answer runs,",
    "pinned RAGAS evaluation, separate Llama comparison and 50-output audit",
    "remain unfinished. These retrieval baselines cannot complete the 28-cell",
    "final experiment matrix. Full narrative scoring requires claim review.",
    "",
    "Chart review",
    "",
    "The user reports that the team reviewed the charts. No reviewer name,",
    "approved item IDs or completed review record has been supplied.",
    "This report records that statement without generating reviewer signatures.",
    "",
    "Reproduce",
    "",
    "Use the existing FinRAG .venv Python and installed BGE/Gemma assets.",
    "python scripts/official_benchmarks/run_evaluation.py          Recompute lexical baseline",
    "python scripts/official_benchmarks/compare_dense.py           Run dense/hybrid retrieval",
    "python scripts/official_benchmarks/run_evaluation.py --pilot  Run three Gemma pilots",
    "python scripts/official_benchmarks/make_report.py             Refresh this report",
    "",
    "See README.md in this report folder for source assets and reproduction settings.",
]
rendered = "\n".join(lines)
(ROOT / "BENCHMARK_RESULTS.txt").write_text("\n".join(line.rstrip() for line in rendered.splitlines()) + "\n")
files = [
    p
    for parent in (ROOT, REPO / "scripts/official_benchmarks")
    for p in parent.rglob("*")
    if p.is_file()
    and p.suffix in (".py", ".json", ".txt", ".md")
    and p.name != "artifact-hashes.json"
    and not any(part.startswith("dense-cache") for part in p.parts)
]
hashes = {str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
(ROOT / "artifact-hashes.json").write_text(json.dumps(hashes, indent=2) + "\n")
print("Report and hashes written.")
