"""Tests for resumable benchmark runner, gate enforcement, and metrics (PRD R7/R12)."""

import json
from unittest.mock import Mock

import pytest

from src.benchmark.loaders import GoldReference
from src.benchmark.metrics import (
    compute_paired_intervals,
    evaluate_numerical_match,
    evaluate_retrieval,
    evaluate_text_match,
)
from src.benchmark.runner import BenchmarkRunner, get_git_revision


def test_git_revision_resolves():
    rev = get_git_revision()
    assert isinstance(rev, str)
    assert len(rev) > 0


def test_manifest_creation_and_control_validation(tmp_path):
    runner = BenchmarkRunner(
        output_dir=tmp_path / "run_test",
        variant="D",
        benchmark="FinQA",
    )
    manifest = runner.init_or_validate_manifest()
    assert manifest.variant == "D"
    assert manifest.benchmark == "FinQA"
    assert manifest.manifest_sha256 != ""
    assert (tmp_path / "run_test" / "run_manifest.json").is_file()

    # Reopening with identical settings should succeed
    runner_reopened = BenchmarkRunner(
        output_dir=tmp_path / "run_test",
        variant="D",
        benchmark="FinQA",
    )
    manifest2 = runner_reopened.init_or_validate_manifest()
    assert manifest2.manifest_sha256 == manifest.manifest_sha256

    # Tampering with saved manifest controls should trigger rejection on resume
    manifest_file = tmp_path / "run_test" / "run_manifest.json"
    tampered_data = json.loads(manifest_file.read_text())
    tampered_data["manifest_sha256"] = "tampered_hash_0000000000"
    manifest_file.write_text(json.dumps(tampered_data))

    runner_tampered = BenchmarkRunner(
        output_dir=tmp_path / "run_test",
        variant="D",
        benchmark="FinQA",
    )
    with pytest.raises(RuntimeError, match="Resumption rejected"):
        runner_tampered.init_or_validate_manifest()


def test_missing_prerequisite_gates_blocks_variant(tmp_path):
    runner = BenchmarkRunner(
        output_dir=tmp_path / "run_g",
        variant="G",
        benchmark="FinanceBench",
        available_gates={"canonical_cells_and_parents"},  # Missing bm25, reranker, chart approval
    )
    summary = runner.run()
    assert summary["status"] == "blocked"
    assert "missing_gates" in summary
    assert "independent_chart_approval" in summary["missing_gates"]
    assert (tmp_path / "run_g" / "summary.json").is_file()


def test_resumable_checkpointing(tmp_path):
    out_dir = tmp_path / "resumable_run"

    # Mock engine that successfully answers
    mock_engine = Mock()
    mock_engine.retriever.variant = "C"
    mock_engine.answer_financial_question.side_effect = lambda question, **kw: {
        "status": "ok",
        "answer": "100,000 million USD",
        "message": "",
        "latency_seconds": 0.05,
        "included_evidence_ids": ["EVID-1", "EVID-2"],
        "retrieval_trace": {"variant": "C", "stages": [{"stage": "dense"}], "routing": "test_routing",
                            "ranked_evidence_ids": ["EVID-1", "EVID-2"]},
        "evidence": [{"content": "100,000 million USD"}],
        "calculations": [],
    }

    # Step 1: Run with max_cases=3
    runner1 = BenchmarkRunner(
        output_dir=out_dir,
        variant="C",
        benchmark="FinanceBench",
        available_gates={"canonical_cells_and_parents"},
        engine=mock_engine,
    )
    summary1 = runner1.run(max_cases=3)
    # 3 of 150 eligible cases is a partial run, never "completed" (F28).
    assert summary1["status"] == "partial"
    assert summary1["eligible_cases"] == 150
    assert summary1["attempted_outputs"] == 3
    assert summary1["not_attempted"] == 147
    assert summary1["final_evaluation_status"] == "BLOCKED_synthetic_smoke_fixture"

    lines = (out_dir / "results.jsonl").read_text().strip().splitlines()
    assert len(lines) == 3
    case_ids_first_run = {json.loads(line)["case_id"] for line in lines}
    assert len(case_ids_first_run) == 3

    # Step 2: Resume with max_cases=5 (should execute 2 additional cases only)
    mock_engine.reset_mock()
    runner2 = BenchmarkRunner(
        output_dir=out_dir,
        variant="C",
        benchmark="FinanceBench",
        available_gates={"canonical_cells_and_parents"},
        engine=mock_engine,
    )
    summary2 = runner2.run(max_cases=5)
    assert summary2["status"] == "partial"
    assert summary2["attempted_outputs"] == 5

    lines2 = (out_dir / "results.jsonl").read_text().strip().splitlines()
    assert len(lines2) == 5
    # The mock engine should have been called only for the remaining 2 cases
    assert mock_engine.answer_financial_question.call_count == 2


def test_metrics_numerical_tolerance():
    gold = GoldReference(
        case_id="T1",
        benchmark="Test",
        gold_answer="100.00",
        gold_value_numeric=100.0,
        relative_tolerance=0.01,  # 1%
        zero_tolerance=0.001,
    )
    # Exactly matching
    assert evaluate_numerical_match("100.00", gold)
    # Within 1% tolerance: 100.9 is 0.9% error
    assert evaluate_numerical_match("100.90", gold)
    # Outside 1% tolerance: 101.5 is 1.5% error
    assert not evaluate_numerical_match("101.50", gold)

    # Zero-gold tolerance
    zero_gold = GoldReference(
        case_id="T0",
        benchmark="Test",
        gold_answer="0.00",
        gold_value_numeric=0.0,
        zero_tolerance=0.001,
    )
    assert evaluate_numerical_match("0.0005", zero_gold)
    assert not evaluate_numerical_match("0.05", zero_gold)


def test_metrics_retrieval_and_exact_match():
    gold = GoldReference(
        case_id="T2",
        benchmark="Test",
        gold_answer="Services Segment",
        gold_evidence_ids=("E1", "E2"),
    )
    assert evaluate_text_match("The revenue came from services segment.", gold)
    assert not evaluate_text_match("Products only.", gold)

    # Retrieval: E1 ranked 1st, E2 ranked 4th
    ranked = ["E1", "X1", "X2", "E2", "X3", "X4"]
    r5, r10, mrr, complete = evaluate_retrieval(ranked, gold.gold_evidence_ids)
    assert r5 == 1.0  # Both E1 and E2 in top 5
    assert r10 == 1.0
    assert mrr == 1.0  # E1 is at rank 1
    assert complete is True


def test_compute_paired_intervals():
    scores_a = [0.8, 0.85, 0.9, 0.75, 0.88]
    scores_b = [0.7, 0.72, 0.8, 0.65, 0.78]
    low, high = compute_paired_intervals(scores_a, scores_b, n_bootstrap=500)
    assert compute_paired_intervals(scores_a, scores_b, n_bootstrap=500) == (low, high)  # fixed seed
    assert low > 0  # A is consistently better than B
    assert high >= low
