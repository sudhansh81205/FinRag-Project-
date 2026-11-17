"""F23/F28/F31/F34 (R7/R12/R13): artifact-bound resume, honest run states, measured capacity, real gates.

Viva: why is hashing a filename different from hashing the model configuration it names, and
what execution trace proves that variant E actually ran a cross-encoder?
"""

import json
from datetime import datetime
from unittest.mock import Mock

import pytest

import src.benchmark.runner as runner_mod
from src.benchmark.capacity import (
    IST,
    compute_capacity,
    measure_machine_capacity,
    validate_observations,
)
from src.benchmark.gates import ALL_GATES, detect_available_gates, evaluate_gates
from src.benchmark.runner import BenchmarkRunner

C_GATES = {"canonical_cells_and_parents"}


def tiny_data(tmp_path, n=3):
    records = [{"case_id": f"T-{i}", "benchmark": "FinanceBench", "question": f"Q{i}?", "company": "Apple Inc.",
                "ticker": "AAPL", "fiscal_year": "2021", "context_text": ["x"], "context_tables": [],
                "gold": {"gold_answer": "100", "gold_evidence_ids": ["E1"]}} for i in range(n)]
    tmp_path.mkdir(parents=True, exist_ok=True)
    path = tmp_path / "tiny.json"
    path.write_text(json.dumps(records), encoding="utf-8")
    return path


def engine_for(variant, with_cross_encoder_stage=True, reranker=True):
    stages = [{"stage": "dense"}] + ([{"stage": "cross_encoder_rerank"}] if with_cross_encoder_stage else [])
    engine = Mock()
    engine.retriever.variant = variant
    engine.retriever.reranker = Mock() if reranker else None
    engine.answer_financial_question.side_effect = lambda question, **kw: {
        "status": "ok", "answer": "100", "message": "", "included_evidence_ids": ["E1"], "evidence": [],
        "retrieval_trace": {"variant": variant, "stages": stages, "ranked_evidence_ids": ["E1"]}}
    return engine


def make_runner(tmp_path, variant="C", gates=C_GATES, engine="auto", **kw):
    if engine == "auto":
        engine = engine_for(variant)
    return BenchmarkRunner(tmp_path / "run", variant=variant, benchmark="FinanceBench",
                           available_gates=gates, engine=engine, data_path=kw.pop("data_path", None) or tiny_data(tmp_path), **kw)


# ---- F23: resume binds actual artifacts --------------------------------------------------------
def test_identical_reopen_is_the_positive_control(tmp_path):
    first = make_runner(tmp_path).init_or_validate_manifest()
    again = make_runner(tmp_path).init_or_validate_manifest()
    assert again.manifest_sha256 == first.manifest_sha256
    assert {"code_sha256", "git_revision", "model_config_sha256", "eligible_case_ids_sha256",
            "prompt_template_sha256", "approved_gates"} <= set(first.identity)


def test_changed_code_is_refused(tmp_path, monkeypatch):
    make_runner(tmp_path).init_or_validate_manifest()
    monkeypatch.setattr(runner_mod, "_code_sha256", lambda: "0" * 64)
    with pytest.raises(RuntimeError, match=r"Resumption rejected.*code_sha256"):
        make_runner(tmp_path).init_or_validate_manifest()


def test_changed_git_revision_is_refused(tmp_path, monkeypatch):
    make_runner(tmp_path).init_or_validate_manifest()
    monkeypatch.setattr(runner_mod, "get_git_revision", lambda: "f" * 40)
    with pytest.raises(RuntimeError, match="git_revision"):
        make_runner(tmp_path).init_or_validate_manifest()


def test_revoked_approvals_are_refused_on_resume(tmp_path):
    make_runner(tmp_path).init_or_validate_manifest()
    with pytest.raises(RuntimeError, match="approved_gates"):
        make_runner(tmp_path, gates=set()).init_or_validate_manifest()


def test_changed_case_set_prompt_and_model_config_are_refused(tmp_path, monkeypatch):
    make_runner(tmp_path).init_or_validate_manifest()
    with pytest.raises(RuntimeError, match="eligible_case_ids_sha256"):
        make_runner(tmp_path, data_path=tiny_data(tmp_path, n=4)).init_or_validate_manifest()
    actual_file_hash = runner_mod._file_sha256
    monkeypatch.setattr(runner_mod, "_file_sha256",
                        lambda p: "e" * 64 if p.name in {"prompts.py", "gemma3-4b.json"} else actual_file_hash(p))
    with pytest.raises(RuntimeError, match=r"model_config_sha256|prompt_template_sha256"):
        make_runner(tmp_path).init_or_validate_manifest()


def test_model_config_content_not_filename_is_bound(tmp_path):
    cfg = tmp_path / "cfg.json"
    cfg.write_text('{"model": "a"}', encoding="utf-8")
    make_runner(tmp_path, model_config_path=cfg).init_or_validate_manifest()
    cfg.write_text('{"model": "b"}', encoding="utf-8")  # same filename, different content
    with pytest.raises(RuntimeError, match="model_config_sha256"):
        make_runner(tmp_path, model_config_path=cfg).init_or_validate_manifest()


def test_edited_saved_controls_are_refused_with_and_without_rehash(tmp_path):
    runner = make_runner(tmp_path)
    runner.init_or_validate_manifest()
    path = runner.manifest_path
    saved = json.loads(path.read_text())
    saved["identity"]["frozen_controls"]["max_passages"] = 999        # stored hash left unchanged
    path.write_text(json.dumps(saved))
    with pytest.raises(RuntimeError, match="does not match its recorded hash"):
        make_runner(tmp_path).init_or_validate_manifest()
    saved["manifest_sha256"] = runner_mod._canonical_sha256(saved["identity"])  # attacker also rehashes
    path.write_text(json.dumps(saved))
    with pytest.raises(RuntimeError, match="frozen_controls"):
        make_runner(tmp_path).init_or_validate_manifest()


def test_legacy_manifest_without_bound_identity_is_refused(tmp_path):
    runner = make_runner(tmp_path)
    runner.manifest_path.write_text(json.dumps({"manifest_sha256": "x", "variant": "C"}))
    with pytest.raises(RuntimeError, match="no bound artifact identity"):
        runner.init_or_validate_manifest()


# ---- F28: honest run states and verified adapters ------------------------------------------------
def test_no_engine_is_blocked_with_no_refusal_ledger(tmp_path):
    runner = make_runner(tmp_path, engine=None)
    summary = runner.run(max_cases=1)
    assert summary["status"] == "blocked_no_engine" and summary["attempted_outputs"] == 0
    assert not runner.results_path.exists()          # nothing a later real run could wrongly resume past
    assert summary["eligible_cases"] == 3


def test_max_cases_is_partial_and_full_run_is_completed_with_denominators(tmp_path):
    runner = make_runner(tmp_path)
    partial = runner.run(max_cases=1)
    assert partial["status"] == "partial" and partial["eligible_cases"] == 3
    assert partial["attempted_outputs"] == 1 and partial["not_attempted"] == 2
    full = make_runner(tmp_path).run()
    assert full["status"] == "completed" and full["attempted_outputs"] == 3 and full["not_attempted"] == 0
    assert full["outcome_counts"] == {"ok": 3, "refused": 0, "failed": 0}
    assert full["final_evaluation_status"] == "BLOCKED_synthetic_smoke_fixture"
    assert full["ragas_status"].startswith("BLOCKED") and full["context_binding"].startswith("UNBOUND")
    assert full["metrics"]["eligible_cases"] == 3


def test_engine_claiming_another_variant_is_blocked(tmp_path):
    summary = make_runner(tmp_path, engine=engine_for("D")).run()
    assert summary["status"] == "blocked_engine_mismatch" and "claimed variant" in summary["message"]


def test_variant_e_requires_cross_encoder_object_and_recorded_stage(tmp_path):
    gates = {"canonical_cells_and_parents", "bm25_index", "bge_reranker_base"}
    no_reranker = make_runner(tmp_path, variant="E", gates=gates, engine=engine_for("E", reranker=False)).run()
    assert no_reranker["status"] == "blocked_engine_mismatch" and "cross-encoder" in no_reranker["message"]

    label_only = make_runner(tmp_path / "b", variant="E", gates=gates,
                             engine=engine_for("E", with_cross_encoder_stage=False))
    summary = label_only.run(max_cases=1)
    assert summary["outcome_counts"] == {"ok": 0, "refused": 0, "failed": 1}   # a label E is not an executed E
    real = make_runner(tmp_path / "c", variant="E", gates=gates, engine=engine_for("E")).run(max_cases=1)
    assert real["outcome_counts"]["ok"] == 1
    ledger = [json.loads(line) for line in (tmp_path / "c" / "run" / "results.jsonl").read_text().splitlines()]
    assert "cross_encoder_rerank" in ledger[0]["engine_stages"] and ledger[0]["input_sha256"]


def test_missing_gates_still_block(tmp_path):
    summary = make_runner(tmp_path, variant="G", gates=C_GATES).run()
    assert summary["status"] == "blocked" and "independent_chart_approval" in summary["missing_gates"]


def test_cli_declares_no_engine_so_a_gate_name_cannot_launch(tmp_path):
    summary = BenchmarkRunner(tmp_path / "cli", variant="C", benchmark="FinQA", available_gates=C_GATES).run()
    assert summary["status"] == "blocked_no_engine"


# ---- F31: capacity is measured or unknown ----------------------------------------------------------------
NOW = datetime(2026, 11, 16, 15, 30, tzinfo=IST)


def test_no_observations_means_unknown_everything(monkeypatch):
    monkeypatch.setattr("src.benchmark.capacity.check_ollama", lambda url: (False, []))
    report = measure_machine_capacity(now=NOW)
    profile = report["machine_profile"]
    assert report["observation_status"] == "unknown" and report["capacity"]["feasibility"] == "unknown"
    assert profile["cold_generation_latency_sec"] is None and profile["warm_generation_latency_sec"] is None
    assert profile["retrieval_latency_sec"] is None and profile["cases_per_hour"] is None
    assert not profile["gemma3_available"] and profile["calculator_eval_latency_sec"] > 0   # real local measurement
    assert report["deadline"]["hours_remaining"] == 32.48 and report["deadline"]["official_cutoff_confirmed"] is False
    assert all(e["estimated_hours"] is None for e in report["capacity"]["suite_estimates"].values())


def test_observed_pilot_produces_a_labelled_measured_estimate(monkeypatch):
    monkeypatch.setattr("src.benchmark.capacity.check_ollama", lambda url: (True, ["gemma3:4b"]))
    pilot = {"cold_generation_sec": 30.0, "warm_generation_sec": 10.0, "retrieval_sec": 1.0, "evaluator_sec": 4.0,
             "pilot_case_ids": ["FB-001"], "measured_at": "2026-11-16T10:00:00+05:30",
             "model_identity": {"gemma3": "sha256:68ceab7e"}}
    report = measure_machine_capacity(observed_timings=pilot, retry_overhead_fraction=0.1, now=NOW)
    cap = report["capacity"]
    assert report["observation_status"] == "observed" and cap["per_case_seconds"] == 15.0
    expected = (150 * 7 * 15.0 * 1.1 + 7 * 30.0) / 3600
    assert cap["suite_estimates"]["financebench_open150_fixture"]["estimated_hours"] == round(expected, 2)
    assert cap["lower_bound"] is False and cap["feasibility"] in {"fits", "does_not_fit"}


def test_missing_evaluator_retry_or_cold_start_is_a_lower_bound_and_missing_core_is_unknown():
    timings = {"retrieval_sec": 1.0, "warm_generation_sec": 10.0, "evaluator_sec": None, "cold_generation_sec": None}
    cap = compute_capacity({"x": 100}, timings, hours_remaining=100.0)
    assert cap["lower_bound"] and len(cap["notes"]) == 3
    assert compute_capacity({"x": 100}, {"retrieval_sec": 1.0}, 100.0)["feasibility"] == "unknown"
    values, problems = validate_observations({"warm_generation_sec": -5, "retrieval_sec": float("inf")})
    assert values["warm_generation_sec"] is None and values["retrieval_sec"] is None and problems


def test_no_fixed_72_hour_window(monkeypatch):
    monkeypatch.setattr("src.benchmark.capacity.check_ollama", lambda url: (False, []))
    later = measure_machine_capacity(now=datetime(2026, 11, 17, 20, 0, tzinfo=IST))
    assert later["deadline"]["hours_remaining"] == 3.98
    assert measure_machine_capacity(now=datetime(2026, 11, 18, 1, 0, tzinfo=IST))["deadline"]["hours_remaining"] == 0.0


# ---- F34: gates come from actual artifacts and explicit acceptance -------------------------------------------
def write_acceptance(root, gate_artifacts, **extra):
    record = {"accepted_by": "Test Reviewer", "accepted_at": "2026-11-16T12:00:00+05:30",
              "gates": {g: {"artifacts": a, **extra} for g, a in gate_artifacts.items()}}
    path = root / "acceptance.json"
    path.write_text(json.dumps(record))
    return path


def sha(path):
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_status_only_report_files_open_no_gate(tmp_path):
    # PR14's detector opened four gates from two tiny status-only JSON files.
    reports = tmp_path / "docs" / "reports"
    reports.mkdir(parents=True)
    (reports / "2026-11-15_chart_promotion_report.json").write_text(json.dumps(
        {"independent_review": "passed", "evaluation_ready": True}))
    (reports / "2026-11-15_corpus_audit.json").write_text(json.dumps({"status": "ai_assisted_accepted"}))
    assert detect_available_gates(root=tmp_path) == set()
    assert all("acceptance record" in r for g in evaluate_gates(tmp_path).values() for r in g["reasons"])


def test_bound_artifact_with_acceptance_opens_gate_then_tamper_and_removal_close_it(tmp_path):
    artifact = tmp_path / "index" / "catalog.json"
    artifact.parent.mkdir()
    artifact.write_text('{"generation": 1}')
    acceptance = write_acceptance(tmp_path, {"bm25_index": {"index/catalog.json": sha(artifact)}})
    assert detect_available_gates(tmp_path, acceptance) == {"bm25_index"}      # positive control
    artifact.write_text('{"generation": 2}')                                    # tampered/stale
    assert "bm25_index" not in detect_available_gates(tmp_path, acceptance)
    artifact.unlink()                                                           # removed after the report exists
    assert evaluate_gates(tmp_path, acceptance)["bm25_index"]["reasons"] == ["Artifact missing: index/catalog.json"]


def test_revoking_the_acceptance_closes_the_gate_on_next_call(tmp_path):
    artifact = tmp_path / "a.bin"
    artifact.write_bytes(b"x")
    acceptance = write_acceptance(tmp_path, {"bm25_index": {"a.bin": sha(artifact)}})
    assert detect_available_gates(tmp_path, acceptance) == {"bm25_index"}
    acceptance.unlink()
    assert detect_available_gates(tmp_path, acceptance) == set()


def test_unfrozen_routing_thresholds_never_open_the_gate(tmp_path):
    artifact = tmp_path / "frozen.json"
    artifact.write_text("{}")
    acceptance = write_acceptance(tmp_path, {"frozen_routing_thresholds": {"frozen.json": sha(artifact)}},
                                  thresholds="unfrozen")
    assert "frozen_routing_thresholds" not in detect_available_gates(tmp_path, acceptance)


def test_repository_has_no_open_gates_without_a_real_acceptance_record():
    assert detect_available_gates() == set()
    assert set(evaluate_gates()) == set(ALL_GATES)


def test_capacity_uses_the_selected_actual_inventory_and_rejects_inconsistent_totals(monkeypatch):
    monkeypatch.setattr("src.benchmark.capacity.check_ollama", lambda url: (False, []))
    inventory = {"benchmarks": {"FinanceBench": {"total_cases": 150}, "FinQA": {"total_cases": 1147},
                              "TAT-QA": {"total_cases": 1663}, "Charts": {"total_cases": 50}},
                 "total_selected_cases": 3010}
    report = measure_machine_capacity(case_inventory=inventory, now=NOW)
    counts = report["suite_inventory"]["selected_actual_counts"]
    assert sum(counts.values()) == 3010 and counts["TAT-QA"] == 1663
    assert report["capacity"]["suite_estimates"]["FinQA"]["cases"] == 1147
    assert report["capacity"]["feasibility"] == "unknown"
    inventory["total_selected_cases"] += 1
    with pytest.raises(ValueError, match="inconsistent"):
        measure_machine_capacity(case_inventory=inventory, now=NOW)
