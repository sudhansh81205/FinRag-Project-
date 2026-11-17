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
