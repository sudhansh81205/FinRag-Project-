"""Tests for interactive Gradio UI flow, session isolation, and fail-closed refusals (R6)."""

import os

os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"
os.environ["HF_HUB_OFFLINE"] = "1"

import pytest

from app import create_demo
from src.application import InteractiveApplication
from src.config import load_settings


@pytest.fixture
def test_app():
    settings = load_settings(environ={
        "FINRAG_HOST": "127.0.0.1",
        "FINRAG_PORT": "7860",
        "FINRAG_PROVIDER": "unconfigured",
        "FINRAG_MODEL": "test-model",
    })
    return InteractiveApplication(settings)


def test_gradio_demo_creates_successfully(test_app):
    demo = create_demo(test_app)
    assert demo is not None
    assert demo.title == "FinRAG"


def test_ui_empty_question_refusal(test_app):
    res = test_app.answer_interactive(question="   ")
    assert res["status"] == "invalid_request"
    assert res["answer"] == ""
    assert "nonempty question" in res["message"]


def test_ui_unindexed_narrative_question_blockers(test_app):
    res = test_app.answer_interactive(question="What was Apple's total net sales in 2021?")
    assert res["status"] == "index_not_ready"
    assert res["answer"] == ""
    assert "No BGE/exact FAISS" in res["message"] or "Answering is disabled" in res["message"]


def test_ui_unapproved_chart_refusal(test_app):
    res = test_app.answer_interactive(
        question="What is shown in this chart?",
        chart_asset_id="ad0ded84e0a5b9dbf96385d1debb0cf711f6f1bec501dda9c067091526dd83a9",
    )
    assert res["status"] == "index_not_ready"
    assert res["answer"] == ""
    assert "candidate-only" in res["message"]
    assert "Ujjwal" in res["message"]


def test_ui_canonical_apple_margin_calculation_success(test_app):
    plan = {
        "issuer": "Apple Inc.",
        "scope": "consolidated",
        "periods": [{"kind": "duration", "start": "2020-09-27", "end": "2021-09-25"}],
        "expression": {
            "op": "ratio_percent",
            "args": [
                {
                    "op": "subtract",
                    "args": [
                        {"evidence_id": "sales"},
                        {"evidence_id": "cost"}
                    ]
                },
                {"evidence_id": "sales"}
            ]
        }
    }
    res = test_app.answer_interactive(
        question="What was Apple's gross margin in fiscal 2021?",
        company="Apple Inc.",
        period_end="2021-09-25",
        calculation_plan=plan,
    )
    assert res["status"] == "ok"
    assert "41.78" in res["answer"]
    assert len(res["calculations"]) == 1
    calc = res["calculations"][0]
    assert calc["status"] == "ok"
    assert calc["unit"] == "percent"
    assert calc["operand_ids"] == ["sales", "cost"]
    assert calc["rule_trace"][-1]["outcome"] == "pass"


def test_ui_calculation_excluded_operand_refusal(test_app):
    # Plan cites an operand 'unknown_tax_expense' not present in included context
    plan = {
        "issuer": "Apple Inc.",
        "scope": "consolidated",
        "periods": [{"kind": "duration", "start": "2020-09-27", "end": "2021-09-25"}],
        "expression": {
            "op": "subtract",
            "args": [
                {"evidence_id": "sales"},
                {"evidence_id": "unknown_tax_expense"}
            ]
        }
    }
    res = test_app.answer_interactive(
        question="What was Apple's net profit after unknown tax?",
        calculation_plan=plan,
    )
    assert res["status"] == "insufficient_evidence"
    assert res["answer"] == ""  # Stale answer must be cleared
    assert "not in included context" in res["message"]
    assert "unknown_tax_expense" in res["message"]


def test_ui_calculation_wrong_period_refusal(test_app):
    # Plan requests 2023 period while included facts are 2021
    plan = {
        "issuer": "Apple Inc.",
        "scope": "consolidated",
        "periods": [{"kind": "duration", "start": "2022-10-01", "end": "2023-09-30"}],
        "expression": {
            "op": "subtract",
            "args": [
                {"evidence_id": "sales"},
                {"evidence_id": "cost"}
            ]
        }
    }
    res = test_app.answer_interactive(
        question="What was margin in 2023?",
        calculation_plan=plan,
    )
    assert res["status"] == "insufficient_evidence"
    assert res["answer"] == ""
    assert "requested_period" in res["message"] or "was not requested" in res["message"]


def test_two_session_client_isolation(test_app):
    """Verify that two concurrent client sessions maintain independent state."""
    # Client Session 1: Apple 2021 Gross Margin
    session_1 = {
        "query_count": 0,
        "last_query": "",
        "last_status": "",
        "session_filters": {},
    }
    plan_1 = {
        "issuer": "Apple Inc.",
        "scope": "consolidated",
        "periods": [{"kind": "duration", "start": "2020-09-27", "end": "2021-09-25"}],
        "expression": {
            "op": "ratio_percent",
            "args": [
                {"op": "subtract", "args": [{"evidence_id": "sales"}, {"evidence_id": "cost"}]},
                {"evidence_id": "sales"}
            ]
        }
    }
    res_1 = test_app.answer_interactive("Apple Q1", company="Apple Inc.", calculation_plan=plan_1)
    session_1["query_count"] += 1
    session_1["last_query"] = "Apple Q1"
    session_1["last_status"] = res_1["status"]
    session_1["session_filters"] = {"company": "Apple Inc.", "period": "2021-09-25"}

    # Client Session 2: Microsoft 2022 Narrative Query
    session_2 = {
        "query_count": 0,
        "last_query": "",
        "last_status": "",
        "session_filters": {},
    }
    res_2 = test_app.answer_interactive("Microsoft Q2", company="Microsoft Corporation")
    session_2["query_count"] += 1
    session_2["last_query"] = "Microsoft Q2"
    session_2["last_status"] = res_2["status"]
    session_2["session_filters"] = {"company": "Microsoft Corporation", "period": "2022-06-30"}

    # Assert Session 1 was not contaminated by Session 2
    assert session_1["last_query"] == "Apple Q1"
    assert session_1["last_status"] == "ok"
    assert session_1["session_filters"]["company"] == "Apple Inc."

    # Assert Session 2 reflects only its own interactions
    assert session_2["last_query"] == "Microsoft Q2"
    assert session_2["last_status"] == "index_not_ready"
    assert session_2["session_filters"]["company"] == "Microsoft Corporation"


def test_stale_output_clearing_on_error(test_app):
    """Verify that an error query immediately clears prior answers and results."""
    # First query succeeds
    plan = {
        "issuer": "Apple Inc.",
        "scope": "consolidated",
        "periods": [{"kind": "duration", "start": "2020-09-27", "end": "2021-09-25"}],
        "expression": {
            "op": "subtract",
            "args": [{"evidence_id": "sales"}, {"evidence_id": "cost"}]
        }
    }
    res1 = test_app.answer_interactive("Apple profit", calculation_plan=plan)
    assert res1["status"] == "ok"
    assert "152836" in res1["answer"]

    # Second query fails (empty question)
    res2 = test_app.answer_interactive("")
    assert res2["status"] == "invalid_request"
    assert res2["answer"] == ""  # Prior answer must NOT persist
    assert res2["calculations"] == []
    assert res2["evidence"] == []
