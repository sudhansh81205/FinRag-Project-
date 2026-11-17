"""R6/R13 web request boundary: real source identity, no default financial success."""
from src.config import load_settings
from src.web_api import WebApplication


def test_supported_request_without_runtime_stays_not_ready():
    app = WebApplication(load_settings(environ={}))
    assert app.health()["status"] == "index_not_ready"
    result = app.answer({"question": "What are the risks?", "ticker": "AAPL",
                         "accession": "0000320193-21-000105", "value_period_end": "2021-09-25",
                         "scope": "consolidated", "mode": "narrative"})
    assert result["status"] == "index_not_ready" and result["answer"] == ""


def test_invalid_web_requests_refuse_before_runtime():
    app = WebApplication(load_settings(environ={}))
    for value in (None, {}, {"question": "x"}, {"question": "What happened?", "accession": "foreign"}):
        assert app.answer(value)["status"] == "invalid_request"


def test_narrative_mode_excludes_unrequested_comparative_numeric_cells():
    class Engine:
        def answer_financial_question(self, **kwargs):
            assert kwargs["top_k_text"] == 5 and kwargs["top_k_tables"] == 0
            assert "calculation_request" not in kwargs
            return {"status": "insufficient_evidence", "message": "No matching narrative"}

    app = WebApplication(load_settings(environ={}), Engine())
    payload = {"question": "What are the risks?", "ticker": "AAPL", "accession": "0000320193-21-000105",
               "value_period_end": "2021-09-25", "scope": "consolidated", "mode": "narrative"}
    assert app.answer(payload)["message"] == "No matching narrative"
    assert app.answer({**payload, "period_kind": "invented"})["status"] == "invalid_request"


def test_review_marks_require_real_identity_timestamp_and_method(tmp_path):
    import json

    import pytest

    from scripts.generate_chart_approvals import load_review_marks

    path = tmp_path / "review.json"
    path.write_text(json.dumps({"cases": [{"id": "c1", "decision": "passed"}]}))
    with pytest.raises(ValueError, match="identity"):
        load_review_marks(path)
    valid = {"cases": [{"id": "c1", "decision": "unreviewed"}], "reviewer_identity": "Independent Person",
             "method": "human_original_image_and_source", "reviewed_at": "2026-11-16T10:00:00+05:30"}
    path.write_text(json.dumps(valid))
    document, marks = load_review_marks(path)
    assert document == valid and marks["c1"]["decision"] == "unreviewed"
    path.write_text(json.dumps({**valid, "reviewed_at": "2999-01-01T00:00:00Z"}))
    with pytest.raises(ValueError, match="timestamp"):
        load_review_marks(path)


def test_web_numerical_planner_uses_only_source_derived_period_boundaries():
    from src.application import make_demo_records
    from src.llm.typed_calculator import evaluate
    from tests.test_nov16_request_binding import PLAN

    class Engine:
        web_source_records = make_demo_records()

        def answer_financial_question(self, question, calculation_plan, filters, calculation_request):
            assert calculation_request == {k: PLAN[k] for k in ("issuer", "scope", "periods")}
            calculation = evaluate(PLAN, self.web_source_records)
            return {"status": "ok", "answer": "untrusted prose", "evidence": self.web_source_records,
                    "calculations": [calculation], "retrieval_trace": {}}

    app = WebApplication(load_settings(environ={}), Engine())
    payload = {"question": "What was gross margin?", "ticker": "AAPL", "accession": "0000320193-21-000105",
               "value_period_end": "2021-09-25", "scope": "consolidated", "mode": "numerical"}
    result = app.answer(payload)
    assert result["status"] == "ok" and "41.78%" in result["answer"]
    result = app.answer({**payload, "value_period_end": "2020-09-26"})
    assert result["status"] == "insufficient_evidence" and result["answer"] == ""


def test_recomputed_program_result_replaces_untrusted_calculation_fields():
    from unittest.mock import Mock

    from src.application import InteractiveApplication, make_demo_records
    from tests.test_nov16_request_binding import PLAN, request_for

    request = request_for("AAPL", 2021)
    engine = Mock()
    engine.answer_financial_question.return_value = {
        "status": "ok", "answer": "forged", "evidence": make_demo_records(),
        "calculations": [{"program": PLAN, "result": "999"}], "retrieval_trace": {}}
    result = InteractiveApplication(load_settings(environ={}), engine).answer_interactive("What was the margin?", request=request)
    assert result["status"] == "ok" and "41.78%" in result["answer"]
    assert result["calculations"][0]["result"] != "999"
    engine.answer_financial_question.return_value["calculations"] = [{"result": "999"}]
    failed = InteractiveApplication(load_settings(environ={}), engine).answer_interactive("What was the margin?", request=request)
    assert failed["status"] == "insufficient_evidence" and failed["answer"] == ""
