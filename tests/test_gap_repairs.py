"""Regression checks for nightly findings F3/F4/F5/F7; no live model calls."""

from unittest.mock import Mock

import pytest

from src.llm.financial_reasoning import FinancialMathVerifier as Math
from src.llm.prompts import build_finrag_prompt
from src.pipeline.finrag_engine import FinRAGEngine
from src.retrieval.retriever import DualHybridRetriever
from tests.test_generation import engine_with, real_stub


def collection():
    return Mock(query=Mock(return_value={"ids": [["source-1"]], "documents": [["complete source"]],
                                         "metadatas": [[{"type": "narrative_text"}]]}))


@pytest.mark.parametrize("query", ["Company culture", "Revenue in 2021"])
@pytest.mark.parametrize("text,tables,expected", [(0, 0, []), (1, 0, [1]), (0, 2, [2])])
def test_disabled_streams_never_query_even_for_numeric_intent(query, text, tables, expected):
    backend, embed = collection(), Mock(return_value=[1, 0])
    result = DualHybridRetriever(backend, embed).retrieve(query, text, tables, force_multimodal=False)
    limits = [call.kwargs["n_results"] for call in backend.query.call_args_list]
    # Qualitative routing may request fewer tables, but never exceeds the caller budget.
    if tables and query == "Company culture":
        expected = [1]
    assert limits == expected
    if not expected:
        embed.assert_not_called()
    else:
        assert (result["text_evidence"] + result["table_evidence"])[0]["id"] == "source-1"


@pytest.mark.parametrize("bad", [{"documents": [["source"]], "metadatas": [[{}]]},
                                  {"ids": [[]], "documents": [["source"]], "metadatas": [[{}]]}])
def test_missing_or_misaligned_index_identity_fails(bad):
    backend = Mock(query=Mock(return_value=bad))
    result = DualHybridRetriever(backend).retrieve("query", 1, 0)
    assert result["text_evidence"] == []
    assert result["text_error"]


def table(identity, content):
    return {"id": identity, "content": content, "metadata": {"type": "financial_table"}}


def test_complete_evidence_selection_matches_prompt_and_ids():
    client = real_stub()
    engine = engine_with([table("large", "X" * 5000), table("small", "UNIQUE-LAST-CELL")], client)
    engine.context_char_budget = 200
    result = engine.answer_financial_question("Revenue?")
    prompt = client.generate.call_args.args[0]
    assert result["status"] == "ok"
    assert result["included_evidence_ids"] == ["small"]
    assert "UNIQUE-LAST-CELL" in prompt and "[Evidence ID: small]" in prompt
    assert "[Evidence ID: large]" not in prompt and "XXXX" not in prompt
    assert result["excluded_evidence"] == [{"id": "large", "reason": "context_budget"}]


def test_large_table_within_budget_is_not_sliced_at_4000():
    client = real_stub()
    result = engine_with([table("complete", "X" * 4500 + "END-MARKER")], client).answer_financial_question("q")
    assert result["included_evidence_ids"] == ["complete"]
    assert "END-MARKER" in client.generate.call_args.args[0]


@pytest.mark.parametrize("records", [[table("too-big", "x" * 100)],
                                     [{"content": "source", "metadata": {"type": "financial_table"}}]])
def test_no_fitting_or_identifiable_evidence_never_generates(records):
    client = real_stub()
    engine = engine_with(records, client)
    engine.context_char_budget = 40
    result = engine.answer_financial_question("q")
    assert result["status"] == "insufficient_evidence"
    client.generate.assert_not_called()


def test_duplicate_and_conflicting_identity_are_not_cited_twice():
    records = [table("one", "first"), table("one", "duplicate"),
               {**table("different", "conflict"), "evidence_id": "canonical"}]
    result = engine_with(records, real_stub()).answer_financial_question("q")
    assert result["included_evidence_ids"] == ["one"]
    assert [x["reason"] for x in result["excluded_evidence"]] == ["duplicate_identity", "conflicting_identity"]


def test_renderer_rejects_oversize_instead_of_silent_slice():
    with pytest.raises(ValueError):
        build_finrag_prompt("q", [], ["x" * 20], max_table_chars=10)
    with pytest.raises(ValueError):
        FinRAGEngine(context_char_budget=0)


def test_negative_prior_has_absolute_change_without_growth_claim():
    result = Math.calculate_yoy_growth(-50, -100)
    assert result["absolute_change"] == 50
    assert result["growth_percentage"] is None
    assert result["formula"] == "-50 - (-100)"
    assert Math.calculate_yoy_growth(120, 100)["growth_percentage"] == 20
    assert Math.calculate_yoy_growth(1, 0)["growth_percentage"] is None
    assert Math.calculate_yoy_growth(float("nan"), 1)["error"]


@pytest.mark.parametrize("raw,expected", [("365817M", 365817000000), ("($2.5B)", -2500000000),
                                         ("12,34", None), ("NaN", None), ("1e9", None),
                                         ("$1,234.50", 1234.5), ("(-5)", None)])
def test_amount_scale_and_invalid_values(raw, expected):
    assert Math.parse_currency_amount(raw) == expected
