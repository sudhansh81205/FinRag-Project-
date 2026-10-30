from src.llm.client import UnifiedLLMClient
from src.llm.financial_reasoning import FinancialMathVerifier
from src.pipeline.finrag_engine import FinRAGEngine


def test_financial_math_verifier():
    # 2021: 365,817 vs 2020: 274,515
    res = FinancialMathVerifier.calculate_yoy_growth(365817, 274515)
    assert res["growth_percentage"] == 33.26
    assert res["absolute_change"] == 91302

    # Currency parser
    parsed = FinancialMathVerifier.parse_currency_amount("$365,817")
    assert parsed == 365817.0
    parsed_neg = FinancialMathVerifier.parse_currency_amount("(2,500)")
    assert parsed_neg == -2500.0


def test_finrag_engine_end_to_end_mock():
    mock_llm = UnifiedLLMClient(provider="mock")
    engine = FinRAGEngine(llm_client=mock_llm)

    response = engine.answer_financial_question("What were Apple's total net sales in 2021?")
    assert "Direct Answer" in response["answer"]
    assert response["provider"] == "mock"
    assert response["latency_seconds"] >= 0
