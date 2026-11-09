"""Real R4/R5/R11 smoke on canonical sources, not retrieval/held-out evaluation.

Run prepare_evidence.py first. Artifacts contain no credentials. A model failure
is saved and causes a nonzero exit; scope shortfalls remain explicit in the report.
"""

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.charts.caption import apply_author_corrections, caption_chart  # noqa: E402
from src.charts.questions import audit_questions  # noqa: E402
from src.llm.client import UnifiedLLMClient  # noqa: E402
from src.llm.typed_calculator import evaluate  # noqa: E402
from src.pipeline.finrag_engine import FinRAGEngine  # noqa: E402


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


class ExplicitEvidence:
    """Already-selected canonical evidence; deliberately not a search experiment."""
    def __init__(self, records):
        self.records = records

    def retrieve(self, **kwargs):
        return {"text_evidence": [], "table_evidence": self.records}


class PreserveSelection:
    def rerank(self, **kwargs):
        return kwargs["candidates"][:kwargs["top_n"]]


class CountCalls:
    def __init__(self, client):
        self.client, self.provider, self.model, self.calls = client, client.provider, client.model, 0
        self.expected_digest = client.expected_digest

    def generate(self, prompt, **kwargs):
        self.calls += 1
        return self.client.generate(prompt, **kwargs)


def leaf(record):
    return {"evidence_id": record["evidence_id"]}


def operation(name, left, right):
    return {"op": name, "args": [left, right]}


def make_plan(expression, records):
    periods = []
    for record in records:
        m = record["metadata"]
        p = {"kind": m["period_kind"], "start": m["period_start"], "end": m["period_end"]}
        if p not in periods:
            periods.append(p)
    return {"issuer": "Apple Inc.", "scope": "consolidated", "periods": periods, "expression": expression}


def run(args):
    started = time.monotonic()
    args.output.mkdir(parents=True, exist_ok=True)
    package_path = args.evidence / "evidence.json"
    package = json.loads(package_path.read_text())
    # Verify source package bytes before consuming records/images.
    manifest = json.loads((args.evidence / "manifest.json").read_text())
    if sha(package_path) != manifest["files_sha256"]["evidence.json"]:
        raise ValueError("Canonical evidence package hash mismatch.")
    profile = json.loads(args.profile.read_text())
    client = UnifiedLLMClient.from_profile(profile)
    counted = CountCalls(client)

    def cell(label, end):
        matches = [r for r in package["cells"] if r["metadata"]["row_label"] == label
                   and r["metadata"]["period_end"] == end
                   and r["metadata"]["table_title"] == "Consolidated Statements of Operations"]
        if len(matches) != 1:
            raise ValueError("Missing/ambiguous canonical operand.")
        return matches[0]

    sales, cost, prior = cell("Total net sales", "2021-09-25"), cell("Total cost of sales", "2021-09-25"), cell("Total net sales", "2020-09-26")
    records = [sales, cost]
    margin = make_plan(operation("ratio_percent", operation("subtract", leaf(sales), leaf(cost)), leaf(sales)), records)
    engine = FinRAGEngine(ExplicitEvidence(records), PreserveSelection(), counted)
    live = engine.answer_financial_question(
        "Calculate Apple's fiscal 2021 gross margin percentage from total net sales and total cost of sales. "
        "Explain the validated result to two decimal places and cite both Evidence IDs.", calculation_plan=margin)
    write(args.output / "live-calculation.json", live)
    automatic = engine.answer_financial_question(
        "What was Apple's fiscal 2021 gross margin percentage, using total net sales and total cost of sales? Cite exact Evidence IDs.",
        calculation_request={k: v for k, v in margin.items() if k != "expression"})
    write(args.output / "live-planned-calculation.json", automatic)
    growth_plan = make_plan(operation("percent_change", leaf(sales), leaf(prior)), [sales, prior])
    growth = evaluate(growth_plan, [sales, prior])
    write(args.output / "source-growth.json", growth)
    before = counted.calls
    refusal = engine.answer_financial_question("Compute gross margin", rerank_top_n=1, calculation_plan=margin)
    write(args.output / "missing-operand.json", refusal)
    failure = UnifiedLLMClient(provider="ollama", ollama_url=client.ollama_url,
                               ollama_model="finrag-deliberately-missing-model:invalid", timeout_seconds=15).generate("Reply briefly.")
    write(args.output / "missing-model.json", failure)
    wrong_digest = UnifiedLLMClient(provider="ollama", ollama_url=client.ollama_url,
                                   ollama_model=client.model, expected_digest="0" * 64).generate("Reply briefly.")
    write(args.output / "wrong-digest.json", wrong_digest)
    captions, raw_captions = [], []
    correction = json.loads((ROOT / "data/charts/apple-2021-author-corrections.json").read_text())
    for source in package["chart_sources"]:
        t = time.monotonic()
        caption = caption_chart(source, args.evidence / source["asset"], client)
        caption["wall_seconds"] = round(time.monotonic() - t, 3)
        raw_captions.append(caption)
        if caption["status"] == "candidate" and source["image_sha256"] == correction["image_sha256"]:
            caption = apply_author_corrections(caption, correction, args.evidence / source["asset"])
        captions.append(caption)
    write(args.output / "chart-model-captions.json", raw_captions)
    write(args.output / "chart-captions.json", captions)
    questions = json.loads((ROOT / "data/charts/apple-2021-candidate-questions.json").read_text())
    known_sources = {s["source_asset_id"]: s["image_sha256"] for s in package["chart_sources"]}
    if any(known_sources.get(q["source_asset_id"]) != q["image_sha256"] for q in questions):
        raise ValueError("Candidate question source differs from canonical source.")
    question_audit = audit_questions(questions)
    write(args.output / "chart-question-audit.json", question_audit)
    import requests
    memory_bytes = (int(subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True))
                    if platform.system() == "Darwin" else os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE"))
    runtime_version = requests.get(client.ollama_url + "/api/version", timeout=15).json()
    loaded = requests.get(client.ollama_url + "/api/ps", timeout=15).json()
    loaded_models = [{k: m.get(k) for k in ("name", "digest", "size", "size_vram", "context_length")}
                     for m in loaded.get("models", [])]
    checks = {
        "real_gemma_answer": live["status"] == "ok" and live["model"] == profile["model"],
        "real_model_planned_typed_tree": automatic["status"] == "ok" and automatic["calculations"][0]["result"] == live["calculations"][0].get("result"),
        "typed_multistep": live["calculations"][0]["status"] == "ok" and live["calculations"][0]["unit"] == "percent",
        "source_growth": growth["status"] == "ok" and growth["unit"] == "percent",
        "missing_operand_skips_model": refusal["status"] == "insufficient_evidence" and counted.calls == before,
        "missing_model_has_no_answer": failure["status"] == "service_error" and not failure["text"],
        "wrong_digest_has_no_answer": wrong_digest.get("error_code") == "digest_mismatch" and not wrong_digest["text"],
        "real_image_captions": bool(captions) and all(c["status"] == "candidate" for c in captions),
    }
    source_files = [ROOT / p for p in (
        "src/llm/calculation_planner.py", "src/config.py", "configs/config.yaml",
        "src/llm/client.py", "src/llm/prompts.py", "src/llm/typed_calculator.py", "src/llm/ollama_profile.py",
        "src/charts/caption.py", "src/charts/questions.py", "src/pipeline/finrag_engine.py",
        "scripts/run_rushil_checks.py", "configs/gemma3-4b.json", "data/charts/apple-2021-candidate-questions.json", "data/charts/apple-2021-author-corrections.json")]
    report = {
        "executed_at": datetime.now(ZoneInfo("Asia/Kolkata")).isoformat(),
        "base_or_current_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "worktree_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
        "source_files_sha256": {str(p.relative_to(ROOT)): sha(p) for p in source_files},
        "evidence_sha256": sha(package_path), "profile_sha256": sha(args.profile),
        "scope": "Real source-selected calculator/generation/vision smoke; no BGE search, A-G evaluation, heldout scores or independent label approval.",
        "model_profile": profile, "hardware": {"machine": platform.machine(), "memory_gib": memory_bytes / 1024 ** 3,
            "python": platform.python_version(), "ollama_version": runtime_version,
            "loaded_model_sizes_api_snapshot_not_peak_host_memory": loaded_models},
        "checks": checks, "passed": all(checks.values()), "chart_scope": question_audit,
        "full_day_scope_complete": False,
        "blockers": ["35 additional heldout chart cases and distinct original images are missing; one image remains entirely dev.",
                     "Chart labels/captions require independent review before evaluation or production G indexing.",
                     "Pavan A-F retrieval/reranker/token budget integration is unavailable on this base.",
                     "Llama3.2 comparison profile is separate and unexecuted; Gemma12B not memory-validated."],
        "wall_seconds": round(time.monotonic() - started, 3)}
    write(args.output / "report.json", report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=ROOT / "data/processed/nov04")
    parser.add_argument("--profile", type=Path, default=ROOT / "configs/gemma3-4b.json")
    parser.add_argument("--output", type=Path, default=ROOT / "output/rushil-nov08")
    args = parser.parse_args()
    try:
        result = run(args)
        print(json.dumps({"passed": result["passed"], "checks": result["checks"], "chart_scope": result["chart_scope"], "wall_seconds": result["wall_seconds"]}, indent=2))
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(2, f"Check could not complete: {type(exc).__name__}; inspect local source/configuration.\n")
    sys.exit(0 if result["passed"] else 1)
