"""R5/R6 common controls: optional interactive prose cannot block licensed math."""
import pytest

from src.pipeline.finrag_engine import FinRAGEngine
from tests.test_named_financial_formulas import facts_and_request


def engine(records):
    class Retriever:
        def retrieve(self, **kwargs):
            return {"all_evidence": records, "ranking_applied": True}

    class Client:
        provider, model = "ollama", "test-fixture-not-live"

        def generate(self, prompt):
            raise RuntimeError("Simulated model timeout; no invented explanation")
    return FinRAGEngine(retriever=Retriever(), llm_client=Client())


def test_interactive_valid_calculation_does_not_depend_on_model_explanation():
    records, request = facts_and_request()
    result = engine(records).answer_financial_question("gross margin?", calculation_request=request,
                                                       skip_calculation_explanation=True)
    assert result["status"] == "ok" and "41.78%" in result["answer"]
    assert result["generation"]["executed"] is False
    assert result["provider"] == "typed_calculator" and result["model"] is None
    assert set(result["calculations"][0]["operand_ids"]) <= set(result["included_evidence_ids"])


def test_matched_default_keeps_real_model_failure_semantics():
    records, request = facts_and_request()
    result = engine(records).answer_financial_question("gross margin?", calculation_request=request)
    assert result["status"] == "service_error" and result["answer"] == ""


def test_calculator_route_does_not_turn_a_mock_engine_into_live_success():
    records, request = facts_and_request()
    app = engine(records)
    app.llm_client.provider = "mock"
    result = app.answer_financial_question("gross margin?", calculation_request=request,
                                             skip_calculation_explanation=True)
    assert result["status"] == "service_error" and result["answer"] == ""


@pytest.mark.parametrize("changed", ["issuer", "missing_operand"])
def test_calculator_route_cannot_bypass_source_premises(changed):
    records, request = facts_and_request()
    if changed == "issuer":
        request = {**request, "issuer": "Foreign company"}
    else:
        records = records[:1]
    result = engine(records).answer_financial_question("gross margin?", calculation_request=request,
                                                       skip_calculation_explanation=True)
    assert result["status"] != "ok" and result["answer"] == ""
