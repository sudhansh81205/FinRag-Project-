"""R6/R11/R13: unavailable inputs refuse before model work; UIs share one lock."""
from types import SimpleNamespace

from src.config import load_settings
from src.web_api import GradioApplication, WebApplication


def test_resume_identity_changes_when_acceptance_record_changes(tmp_path):
    import pytest

    from tests.test_nov16_runner_capacity_gates import make_runner

    path = tmp_path / "docs/reports/2026-11-16_gate_acceptance.json"
    path.parent.mkdir(parents=True)
    path.write_text('{"fixture":"not a human approval"}')
    runner = make_runner(tmp_path)
    runner.settings = SimpleNamespace(root=tmp_path, index_dir=tmp_path / "index")
    runner.init_or_validate_manifest()
    path.write_text('{"fixture":"changed, still not a human approval"}')
    with pytest.raises(RuntimeError, match="acceptance_record_sha256"):
        runner.init_or_validate_manifest()


def test_total_revenue_cannot_use_a_product_sales_component():
    import copy

    from src.application import make_demo_records
    from src.llm.financial_semantics import known_source_program, validate_named_formula
    from tests.test_nov16_request_binding import PLAN

    total = make_demo_records()[0]
    total["metadata"]["row_headers"] = ["Total net sales"]
    component = copy.deepcopy(total)
    component["evidence_id"] = "product-sales-fixture"
    component["metadata"]["row_headers"] = ["Net sales", "Products"]
    question = "How much revenue did Apple report in fiscal year 2021?"
    request = {key: PLAN[key] for key in ("issuer", "scope", "periods")}
    program = known_source_program(question, request, [component, total])
    assert program["expression"] == {"evidence_id": total["evidence_id"]}
    assert not validate_named_formula(question, program, [component, total])
    program["expression"] = {"evidence_id": component["evidence_id"]}
    assert "component" in validate_named_formula(question, program, [component, total])
    assert known_source_program(question, request, [component]) is None


def test_inventory_filing_refuses_without_calling_model():
    class Engine:
        web_source_records = [{"metadata": {"accession": "0000320193-21-000105"}}]

        def answer_financial_question(self, **kwargs):
            raise AssertionError("Unavailable source must not call the model")

    web = WebApplication(load_settings(environ={}), Engine())
    assert web.health()["supported_filings"] == ["0000320193-21-000105"]
    result = web.answer({"question": "What are the risks?", "ticker": "AAPL",
                         "accession": "0000320193-22-000108", "value_period_end": "2022-09-24",
                         "scope": "consolidated", "mode": "narrative"})
    assert result["status"] == "index_not_ready" and result["answer"] == ""
    assert not web.health()["modes"]["chart"]


def test_gradio_cannot_call_model_while_web_holds_lock():
    web = WebApplication(load_settings(environ={}))
    gradio = GradioApplication(web)
    request = SimpleNamespace(ticker="AAPL", accession="0000320193-21-000105",
                              value_period_end="2021-09-25", scope="consolidated")
    web._answer_lock.acquire()
    try:
        for plan in (None, {"expression": {}}):
            result = gradio.answer_interactive("What are the risks?", request=request,
                                               calculation_plan=plan)
            assert result["status"] == "service_error" and result["answer"] == ""
    finally:
        web._answer_lock.release()
    assert gradio.answer_interactive("What are the risks?")["status"] == "invalid_request"


def test_gradio_bridge_preserves_request_constraints():
    web = WebApplication(load_settings(environ={}))
    seen = []
    web.answer = lambda payload: seen.append(payload) or {"status": "insufficient_evidence", "answer": ""}
    request = SimpleNamespace(ticker="AAPL", accession="0000320193-21-000105",
                              value_period_end="2021-09-25", scope="consolidated")
    result = GradioApplication(web).answer_interactive("What is revenue?", request=request)
    assert result["status"] == "insufficient_evidence"
    assert seen == [{"question": "What is revenue?", "ticker": "AAPL", "accession": request.accession,
                     "value_period_end": "2021-09-25", "scope": "consolidated", "mode": "auto"}]
