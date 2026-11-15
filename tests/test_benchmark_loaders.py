"""Unit tests for versioned benchmark loaders and strict gold separation (PRD R7)."""

import pytest

from src.benchmark.loaders import (
    load_benchmark,
    load_financebench_open150,
    load_finqa,
    load_tatqa,
    verify_gold_separation,
)


def test_load_financebench_open150():
    suite = load_financebench_open150()
    assert len(suite) == 150

    case_ids = set()
    for case, gold in suite:
        assert case.benchmark == "FinanceBench"
        assert case.case_id.startswith("FB-")
        assert case.case_id not in case_ids, f"Duplicate ID: {case.case_id}"
        case_ids.add(case.case_id)

        assert case.question and isinstance(case.question, str)
        assert case.company and isinstance(case.company, str)
        assert case.doc_name and isinstance(case.doc_name, str)

        # Context must contain narrative text and tables
        assert len(case.context_text) > 0
        assert len(case.context_tables) > 0

        # Gold reference checks
        assert gold.case_id == case.case_id
        assert gold.gold_answer != ""

        # Strict gold separation check
        eval_input = case.to_eval_input()
        assert verify_gold_separation(eval_input)
        assert "gold" not in eval_input
        assert "gold_answer" not in eval_input


def test_load_finqa_candidate_universe():
    suite = load_finqa()
    assert len(suite) == 50

    for case, gold in suite:
        assert case.benchmark == "FinQA"
        assert case.case_id.startswith("FINQA-")
        assert case.question_type == "arithmetic"
        assert len(case.context_tables) > 0

        # Gold program check
        assert gold.gold_program is not None
        assert "op" in gold.gold_program
        assert gold.gold_value_numeric is not None

        # Separation
        eval_input = case.to_eval_input()
        assert verify_gold_separation(eval_input)


def test_load_tatqa_candidate_universe():
    suite = load_tatqa()
    assert len(suite) == 50

    q_types = {case.question_type for case, _ in suite}
    assert {"arithmetic", "span", "multi-span", "count"}.issubset(q_types)

    for case, gold in suite:
        assert case.benchmark == "TAT-QA"
        assert case.case_id.startswith("TATQA-")
        assert len(case.context_text) > 0

        eval_input = case.to_eval_input()
        assert verify_gold_separation(eval_input)


def test_unified_load_benchmark_dispatch():
    fb = load_benchmark("FinanceBench")
    assert len(fb) == 150

    finqa = load_benchmark("FinQA")
    assert len(finqa) == 50

    tatqa = load_benchmark("TAT-QA")
    assert len(tatqa) == 50

    with pytest.raises(ValueError, match="Unknown benchmark"):
        load_benchmark("UnsupportedBenchmark")


def test_gold_separation_rejects_leaked_target():
    leaked = {
        "case_id": "TEST-01",
        "question": "What is revenue?",
        "gold_answer": "100 million",
    }
    assert not verify_gold_separation(leaked)

    clean = {
        "case_id": "TEST-01",
        "question": "What is revenue?",
        "context_text": ["Revenue was 100 million."],
    }
    assert verify_gold_separation(clean)
