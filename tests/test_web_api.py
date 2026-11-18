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
    assert app.answer({**payload, "mode": "auto"})["message"] == "No matching narrative"
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

        def answer_financial_question(self, question, calculation_plan, filters, calculation_request, **options):
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


def test_sync_and_job_entry_points_never_run_the_model_concurrently():
    import threading

    entered, release = threading.Event(), threading.Event()

    class Engine:
        def answer_financial_question(self, **kwargs):
            entered.set()
            assert release.wait(5)
            return {"status": "insufficient_evidence", "message": "No matching narrative"}

    app = WebApplication(load_settings(environ={}), Engine())
    payload = {"question": "What are the risks?", "ticker": "AAPL", "accession": "0000320193-21-000105",
               "value_period_end": "2021-09-25", "scope": "consolidated", "mode": "narrative"}
    results = []
    worker = threading.Thread(target=lambda: results.append(app.answer(payload)))
    worker.start()
    try:
        assert entered.wait(3)
        busy = app.answer(payload)
        assert busy["status"] == "service_error" and busy["answer"] == ""
        assert busy["evidence"] == []
    finally:
        release.set()
        worker.join(5)
    assert not worker.is_alive() and results[0]["status"] == "insufficient_evidence"
    assert app.answer(payload)["status"] == "insufficient_evidence"


def test_employee_headcount_uses_original_filing_not_monetary_planner():
    class Engine:
        web_source_records = [{"metadata": {"accession": "0000858877-24-000017"}}]

        def answer_financial_question(self, **kwargs):
            raise AssertionError("Count requests must never use an unrelated monetary fact")

    app = WebApplication(load_settings(environ={}), Engine())
    payload = {
        "question": "how many total employees in cisco as of july 2024",
        "ticker": "CSCO", "accession": "0000858877-24-000017", "value_period_end": "2024-07-27",
        "scope": "consolidated", "mode": "auto", "period_kind": "duration",
    }
    answer = app.answer(payload)
    assert answer["status"] == "ok" and "approximately 90,400 employees" in answer["answer"]
    assert answer["request"]["accession"] == payload["accession"]
    assert answer["request"]["period_kind"] == payload["period_kind"]
    evidence, = answer["evidence"]
    assert evidence["metadata"]["raw_unit"] == "employees"
    assert evidence["metadata"]["period_end"] == "2024-07-27"
    assert evidence["metadata"]["section"] == "Item 1"
    assert "90,400 employees" in evidence["content"]
    assert answer["included_evidence_ids"] == [evidence["evidence_id"]]
    assert not answer["calculations"]

    other = app.answer({**payload, "question": "How many employees did Cisco have as of July 27, 2024?",
                        "mode": "numerical", "period_kind": "instant"})
    assert other["status"] == "ok" and other["answer"] == answer["answer"]
    for question in (
        "How many employees did Cisco have in the United States in July 2024?",
        "How many employees did Cisco have as of July 31, 2024?",
        "How many employees did Cisco have as of July 2023?",
        "How many offices did Cisco have in FY2024?",
    ):
        refused = app.answer({**payload, "question": question})
        assert refused["status"] == "insufficient_evidence" and not refused["answer"] and not refused["evidence"]


def test_product_amount_requires_its_own_source_and_cannot_use_company_total():
    class Engine:
        web_source_records = [
            {"metadata": {"accession": "0000320193-25-000079"}},
            {"metadata": {"accession": "0000950170-25-100235"}},
        ]

        def answer_financial_question(self, **kwargs):
            raise AssertionError("Product disclosures must never use a consolidated total")

    app = WebApplication(load_settings(environ={}), Engine())
    apple = {
        "question": "How much revenue did Apple report from iPhone in FY2025?",
        "ticker": "AAPL", "accession": "0000320193-25-000079", "value_period_end": "2025-09-27",
        "scope": "consolidated", "mode": "auto", "period_kind": "duration",
    }
    answer = app.answer(apple)
    assert answer["status"] == "ok" and "$209,586,000,000" in answer["answer"]
    evidence, = answer["evidence"]
    assert evidence["metadata"]["dimensions"] == {"srt:ProductOrServiceAxis": "aapl:IPhoneMember"}
    assert evidence["metadata"]["scope"] == "product"
    assert app.answer({**apple, "question": "How much revenue did Apple report from iPhone in China in FY2025?"})["status"] == "insufficient_evidence"
    azure = app.answer({
        **apple, "question": "How much revenue did Microsoft report from Azure in FY2025?",
        "ticker": "MSFT", "accession": "0000950170-25-100235", "value_period_end": "2025-06-30",
    })
    assert azure["status"] == "insufficient_evidence" and not azure["answer"] and not azure["evidence"]
