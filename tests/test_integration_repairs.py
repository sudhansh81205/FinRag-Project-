"""R3/R4/R10/R12 safety controls on combined PRs; all providers are injected fixtures."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.pipeline.finrag_engine import FinRAGEngine
from src.retrieval.reranker import SimpleFinancialReranker
from tests.test_generation import engine_with, real_stub


def record(identity):
    return {"id": identity, "content": f"Source value {identity}",
            "metadata": {"type": "narrative_text"}}


@pytest.mark.parametrize("reply", [{"rerank_error": "secret backend error"},
                                 {"error_code": "missing_model"},
                                 {"status": "service_error", "all_evidence": []},
                                 {"failure_code": "missing_model"}, None])
def test_failed_retrieval_never_becomes_provider_success(reply):
    client = real_stub()
    engine = engine_with([record("source")], client)
    engine.retriever.retrieve.return_value = reply
    result = engine.answer_financial_question("question")
    assert result["status"] == "service_error" and not result["answer"]
    assert "secret backend error" not in str(result)
    client.generate.assert_not_called()


def test_canonical_ranking_keeps_cross_stream_order_without_second_rerank():
    client = real_stub()
    engine = engine_with([], client)
    candidates = [record(str(i)) for i in range(7)]
    engine.retriever.retrieve.return_value = {
        "all_evidence": candidates, "ranking_applied": True, "variant": "D",
        "ranked_evidence_ids": [r["id"] for r in candidates],
    }
    result = engine.answer_financial_question("question", rerank_top_n=20,
                                             filters={"ticker": "AAPL"})
    assert result["status"] == "ok"
    assert result["included_evidence_ids"] == [str(i) for i in range(5)]
    assert result["passage_selection"]["target"] == 5
    assert result["passage_selection"]["shortfall"] == 0
    assert result["retrieval_trace"]["variant"] == "D"
    assert [r["reason"] for r in result["excluded_evidence"]] == ["passage_limit"] * 2
    engine.reranker.rerank.assert_not_called()
    assert engine.retriever.retrieve.call_args.kwargs["filters"] == {"ticker": "AAPL"}


def test_explicit_tokenizer_selects_complete_objects_and_records_shortfall():
    client = real_stub()
    engine = engine_with([record("a"), record("b")], client)
    # Test counter counts whole ID-marked objects, not real model tokens.
    engine.token_counter = lambda text: text.count("[Evidence ID:")
    engine.context_token_budget = 1
    engine.tokenizer_id = "synthetic-object-counter-not-a-model-tokenizer"
    result = engine.answer_financial_question("question")
    assert result["status"] == "ok"
    assert result["included_evidence_ids"] == ["a"]
    assert result["context_budget"]["used"] == 1
    assert result["context_budget"]["unit"] == "tokens"
    assert result["passage_selection"]["shortfall"] == 4
    assert "[Evidence ID: b]" not in client.generate.call_args.args[0]
    assert result["passage_selection"]["final_experiment_ready"] is False


@pytest.mark.parametrize("kwargs", [
    {"context_token_budget": 10},
    {"context_token_budget": True, "token_counter": len, "tokenizer_id": "fixture"},
    {"context_token_budget": 10, "token_counter": len},
    {"token_counter": len},
])
def test_token_budget_never_guesses_a_tokenizer(kwargs):
    with pytest.raises(ValueError, match="token"):
        FinRAGEngine(**kwargs)


@pytest.mark.parametrize("scores", [[1], [1, float("nan")], [1, float("inf")],
                                    [1, "bad"], [1, "2"], [True, 2]])
def test_legacy_reranker_also_rejects_partial_nonfinite_scores_without_mutation(scores):
    candidates = [record("a"), record("b")]
    reranker = SimpleFinancialReranker(Mock(predict=Mock(return_value=scores)))
    with pytest.raises(ValueError):
        reranker.rerank("question", candidates)
    assert all("rerank_score" not in candidate for candidate in candidates)


def test_legacy_valid_cross_encoder_scores_rank_copies():
    candidates = [record("a"), record("b")]
    reranker = SimpleFinancialReranker(Mock(predict=Mock(return_value=[1, 2])))
    assert [r["id"] for r in reranker.rerank("question", candidates)] == ["b", "a"]
    assert all("rerank_score" not in candidate for candidate in candidates)


def test_typed_stage_exception_preserves_failure_trace_and_blocks_generation():
    from src.retrieval.bm25 import RetrievalStageError

    client = real_stub()
    engine = engine_with([], client)
    engine.retriever.retrieve.side_effect = RetrievalStageError(
        "cross_encoder_failed", "E", {"variant": "E", "stage": "cross_encoder"})
    result = engine.answer_financial_question("question")
    assert result["status"] == "service_error"
    assert result["error_code"] == "cross_encoder_failed"
    assert result["failed_stage"] == "E"
    assert result["retrieval_trace"]["variant"] == "E"
    client.generate.assert_not_called()


def test_exact_engine_assembly_queries_real_faiss_without_legacy_collection(tmp_path):
    import numpy as np

    from src.application import assemble_exact_engine
    from src.config import load_settings
    from src.indexing.bge import EmbeddingSpec
    from src.indexing.store import ExactStore, publish_filing
    from tests.test_exact_index import record as canonical_record

    matrix = np.zeros((1, 768), dtype=np.float32)
    matrix[0, 0] = 1
    publish_filing(tmp_path, [canonical_record("synthetic")], [], matrix, {"test_only": True})
    store = ExactStore(tmp_path)
    encoder = SimpleNamespace(spec=EmbeddingSpec(), encode=Mock(return_value=matrix))
    client = real_stub()
    engine = assemble_exact_engine(load_settings(environ={}), store=store, encoder=encoder,
                                  llm_client=client, variant="D")
    answer = engine.answer_financial_question("synthetic", top_k_tables=0,
                                             filters={"ticker": "AAPL"})
    assert answer["status"] == "ok"
    assert answer["included_evidence_ids"] == [store.records[0]["evidence_id"]]
    assert answer["retrieval_trace"]["variant"] == "D"
    assert answer["retrieval_trace"]["ranking_applied"] is True
    # A successive request must not reuse a prior company's evidence or answer.
    client.generate.reset_mock()
    missing = engine.answer_financial_question("synthetic", top_k_tables=0,
                                               filters={"ticker": "MSFT"})
    assert missing["status"] == "insufficient_evidence" and missing["answer"] == ""
    client.generate.assert_not_called()


@pytest.mark.parametrize("filters", [{"unknown": "field"}, {"ticker": True}, ["AAPL"]])
def test_bad_request_filters_are_invalid_input_before_any_retrieval(filters):
    client = real_stub()
    engine = engine_with([], client)
    result = engine.answer_financial_question("question", filters=filters)
    assert result["status"] == "invalid_request"
    engine.retriever.retrieve.assert_not_called()
    client.generate.assert_not_called()


def test_calculation_prompt_retains_every_included_chart_object():
    import hashlib

    from tests.test_typed_calculator import fact, leaf, op, plan

    content = "SYNTHETIC reviewed chart description; exact curve values unknown."
    chart = {"evidence_id": "fixture-chart", "content": content,
        "source": {"image_sha256": "a" * 64, "pdf_url": "https://example.org/fixture.pdf",
                   "page": 1, "source_asset_id": "fixture-asset"},
        "metadata": {"type": "chart_description", "independent_review": "passed",
                     "generated": True, "image_sha256": "a" * 64,
                     "content_sha256": hashlib.sha256(content.encode()).hexdigest()}}
    client = real_stub()
    engine = engine_with([fact("sales", 30), fact("cost", 10, metric="Cost"), chart], client)
    engine.enable_chart_descriptions = True
    result = engine.answer_financial_question("Gross profit?", calculation_plan=plan(
        op("subtract", leaf("sales"), leaf("cost"))))
    assert result["status"] == "ok"
    prompt = client.generate.call_args.args[0]
    assert content in prompt and "[Evidence ID: fixture-chart]" in prompt
    assert result["included_evidence_ids"] == ["sales", "cost", "fixture-chart"]
    assert result["calculations"][0]["operand_ids"] == ["sales", "cost"]
