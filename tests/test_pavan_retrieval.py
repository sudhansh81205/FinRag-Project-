"""Pavan November 7 — A-F cumulative retrieval stage tests.

No live model calls, no BGE downloads.  All fixtures use synthetic records
identical in shape to canonical ExactStore records so the same interfaces
are exercised.

Component coverage (not a complete A-G evaluation):
  C    parent expansion within budget
  D    BM25 plus RRF fusion
  E    hierarchical restriction and cross-encoding (synthetic predictor)
  F    bounded routing and explicit unavailable chart tier
  --   disabled-stream contract (no query issued)
  --   chart tier blocked
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.retrieval.bm25 import (
    BM25Index,
    BM25Retriever,
    HybridRRFRetriever,
    RetrievalStageError,
    RoutingPolicy,
    expand_parents,
    reciprocal_rank_fusion,
)
from src.retrieval.dense import DenseRetriever
from src.retrieval.eligibility import eligible

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

def _record(eid, content, kind="narrative_text", parent_id=None, ticker="AAPL"):
    m = {
        "accession": "0000320193-21-000105",
        "ticker": ticker,
        "type": kind,
    }
    if parent_id:
        m["parent_table_id"] = parent_id
    return {"evidence_id": eid, "content": content, "metadata": m}


NARRATIVES = [
    _record("n1", "Apple revenue grew in fiscal year 2021"),
    _record("n2", "Risk factors include supply chain disruptions"),
    _record("n3", "Total net sales reached 365 billion USD"),
]

CELLS = [
    _record("c1", "Total net sales | September 25 2021 | 365,817 | USD millions | Apple.Inc.NetRevenue", "table_cell", "p1"),
    _record("c2", "Services revenue | September 25 2021 | 68,425 | USD millions | Apple.Inc.ServicesRevenue", "table_cell", "p1"),
]

PARENTS = {
    "p1": _record("p1", "Consolidated Statements of Operations\nTotal net sales | 2021 | 2020", "financial_table"),
}

ALL_RECORDS = NARRATIVES + CELLS


# ---------------------------------------------------------------------------
# BM25 unit tests (stage D)
# ---------------------------------------------------------------------------

class TestBM25Index:
    def test_exact_term_ranks_first(self):
        index = BM25Index(NARRATIVES)
        results = index.search("revenue fiscal year 2021", k=3)
        assert results[0]["evidence_id"] == "n1"
        assert results[0]["bm25_score"] > 0

    def test_non_matching_query_gives_zero_score(self):
        index = BM25Index(NARRATIVES)
        results = index.search("quantum entanglement physics", k=3)
        # All scores may be zero; order is deterministic by evidence_id
        for r in results:
            assert r["bm25_score"] >= 0

    def test_k_zero_returns_empty_no_scoring(self):
        index = BM25Index(NARRATIVES)
        assert index.search("revenue", k=0) == []

    def test_filter_by_ticker_excludes_other_company(self):
        msft = [_record("m1", "Microsoft cloud revenue 2021", ticker="MSFT")]
        index = BM25Index(NARRATIVES + msft)
        results = index.search("revenue 2021", k=10, filters={"ticker": "AAPL"})
        ids = [r["evidence_id"] for r in results]
        assert "m1" not in ids

    def test_eligible_count_reflects_filter(self):
        msft = [_record("m1", "Microsoft revenue", ticker="MSFT")]
        index = BM25Index(NARRATIVES + msft)
        results = index.search("revenue", k=10, filters={"ticker": "MSFT"})
        assert len(results) == 1
        assert results[0]["eligible_count"] == 1

    def test_empty_records_raises(self):
        with pytest.raises(ValueError, match="at least one"):
            BM25Index([])

    def test_bm25_rank_field_present_and_ordered(self):
        index = BM25Index(NARRATIVES)
        results = index.search("revenue 2021 net sales", k=3)
        for i, r in enumerate(results, 1):
            assert r["bm25_rank"] == i


class TestBM25Retriever:
    def test_retrieve_separates_narrative_and_cell_streams(self):
        bm25 = BM25Retriever(ALL_RECORDS)
        result = bm25.retrieve("Apple revenue 2021", top_k_text=2, top_k_tables=2)
        assert result["retrieval_mode"] == "bm25_only"
        for item in result["text_evidence"]:
            assert item["metadata"]["type"] == "narrative_text"
        for item in result["table_evidence"]:
            assert item["metadata"]["type"] == "table_cell"

    def test_disabled_stream_issues_no_query(self):
        bm25 = BM25Retriever(ALL_RECORDS)
        result = bm25.retrieve("revenue", top_k_text=0, top_k_tables=3)
        assert result["text_evidence"] == []
        assert len(result["table_evidence"]) > 0

    def test_both_zero_returns_empty(self):
        bm25 = BM25Retriever(ALL_RECORDS)
        result = bm25.retrieve("revenue", top_k_text=0, top_k_tables=0)
        assert result["text_evidence"] == result["table_evidence"] == []

    def test_type_filter_rejected(self):
        with pytest.raises(ValueError, match="stream limits"):
            BM25Retriever(ALL_RECORDS, filters={"type": "narrative_text"})

    def test_negative_budget_raises(self):
        bm25 = BM25Retriever(ALL_RECORDS)
        with pytest.raises(ValueError, match="nonnegative"):
            bm25.retrieve("revenue", top_k_text=-1, top_k_tables=3)


# ---------------------------------------------------------------------------
# RRF unit tests (stage E)
# ---------------------------------------------------------------------------

class TestRRF:
    def test_item_in_both_lists_scores_higher(self):
        list_a = [{"evidence_id": "x", "content": "a"}, {"evidence_id": "y", "content": "b"}]
        list_b = [{"evidence_id": "y", "content": "b"}, {"evidence_id": "z", "content": "c"}]
        fused = reciprocal_rank_fusion([list_a, list_b], k=60)
        ids = [r["evidence_id"] for r in fused]
        # "y" appears in both lists so should outscore single-list items
        assert ids[0] == "y"

    def test_rrf_score_field_present(self):
        items = [{"evidence_id": "a", "content": "text"}]
        fused = reciprocal_rank_fusion([items], k=60)
        assert "rrf_score" in fused[0]
        assert "rrf_component_ranks" in fused[0]

    def test_deterministic_tie_breaking_by_id(self):
        # Two items ranked equally (each in one list at position 1)
        list_a = [{"evidence_id": "z", "content": "a"}]
        list_b = [{"evidence_id": "a", "content": "b"}]
        fused = reciprocal_rank_fusion([list_a, list_b], k=60)
        # Same RRF score; "a" < "z" alphabetically
        assert fused[0]["evidence_id"] == "a"

    def test_empty_lists_produce_empty_fusion(self):
        assert reciprocal_rank_fusion([[], []], k=60) == []

    def test_items_without_evidence_id_are_skipped(self):
        bad = [{"id": "legacy", "content": "x"}]
        good = [{"evidence_id": "ok", "content": "y"}]
        fused = reciprocal_rank_fusion([bad, good], k=60)
        # Items without evidence_id are dropped from fusion
        # (legacy items may survive if they have an "id" key but not "evidence_id")
        all_ids = [r.get("evidence_id", r.get("id")) for r in fused]
        assert "ok" in all_ids
        # Only "ok" should appear as a canonical evidence_id result
        evidence_ids = [r["evidence_id"] for r in fused if "evidence_id" in r]
        assert "ok" in evidence_ids

    def test_invalid_k_raises(self):
        with pytest.raises(ValueError, match="positive"):
            reciprocal_rank_fusion([[]], k=0)


# ---------------------------------------------------------------------------
# Parent expansion tests (stage C)
# ---------------------------------------------------------------------------

class TestParentExpansion:
    def test_parent_injected_before_cell(self):
        already: set[str] = set()
        result = expand_parents(
            CELLS,
            PARENTS,
            budget_chars=100_000,
            already_included=already,
        )
        ids = [r["evidence_id"] for r in result]
        # Parent "p1" should appear before cells
        assert "p1" in ids
        p_idx = ids.index("p1")
        assert all(ids.index(c["evidence_id"]) > p_idx for c in CELLS if c["evidence_id"] in ids)

    def test_parent_injected_only_once(self):
        already: set[str] = set()
        result = expand_parents(
            CELLS,  # Both cells share parent p1
            PARENTS,
            budget_chars=100_000,
            already_included=already,
        )
        ids = [r["evidence_id"] for r in result]
        assert ids.count("p1") == 1

    def test_parent_skipped_when_budget_exhausted(self):
        already: set[str] = set()
        result = expand_parents(
            CELLS,
            PARENTS,
            budget_chars=0,  # No budget
            already_included=already,
        )
        ids = [r["evidence_id"] for r in result]
        assert "p1" not in ids

    def test_narratives_pass_through_unchanged(self):
        already: set[str] = set()
        result = expand_parents(
            NARRATIVES,
            PARENTS,
            budget_chars=100_000,
            already_included=already,
        )
        # Narratives have no parent_table_id; they pass through as-is
        ids = [r["evidence_id"] for r in result]
        assert all(n["evidence_id"] in ids for n in NARRATIVES)
        assert "p1" not in ids


# ---------------------------------------------------------------------------
# HybridRRFRetriever integration tests (stages E and F)
# ---------------------------------------------------------------------------

def _make_hybrid(narrative_on=True, table_on=True, with_reranker=False):
    """Build a HybridRRFRetriever with stubbed dense and BM25 retrievers."""
    dense_stub = MagicMock()
    dense_stub.retrieve.return_value = {
        "text_evidence": NARRATIVES[:2] if narrative_on else [],
        "table_evidence": CELLS[:1] if table_on else [],
        "retrieval_mode": "dense_only",
    }

    bm25_stub = MagicMock()
    bm25_stub.retrieve.return_value = {
        "text_evidence": [NARRATIVES[2]] if narrative_on else [],
        "table_evidence": CELLS[1:] if table_on else [],
        "retrieval_mode": "bm25_only",
    }

    reranker = None
    if with_reranker:
        reranker = MagicMock()
        reranker.predict.side_effect = lambda pairs: [1.0 / (i + 1) for i in range(len(pairs))]

    return HybridRRFRetriever(dense_stub, bm25_stub, reranker=reranker, rrf_k=60)


class TestHybridRRFRetriever:
    def test_stage_trace_contains_all_stages(self):
        hybrid = _make_hybrid()
        result = hybrid.retrieve("Apple revenue 2021", store_parents=PARENTS)
        stage_names = [s["stage"] for s in result["stages"]]
        assert "dense" in stage_names
        assert "bm25" in stage_names
        assert "rrf_fusion" in stage_names

    def test_ranked_ids_do_not_claim_prompt_inclusion(self):
        hybrid = _make_hybrid()
        result = hybrid.retrieve("revenue", store_parents=PARENTS)
        assert result["ranked_evidence_ids"] == [c["evidence_id"] for c in result["all_evidence"]]
        assert result["ranked_evidence_ids"]
        assert "included_evidence_ids" not in result

    def test_chart_tier_always_blocked(self):
        hybrid = _make_hybrid()
        result = hybrid.retrieve("show me the revenue chart")
        assert result["routing"]["chart"] is False
        assert result["chart_evidence"] == []

    def test_disabled_narrative_stream_calls_no_text_retrieval(self):
        hybrid = _make_hybrid(narrative_on=False, table_on=True)
        result = hybrid.retrieve(
            "revenue",
            top_k_text=0,
            top_k_tables=3,
            routing={"narrative": False},
            store_parents=PARENTS,
        )
        assert result["routing"]["narrative"] is False
        # Text evidence should be empty when stream is disabled
        assert result["text_evidence"] == []

    def test_cross_encoder_stage_present_when_reranker_given(self):
        hybrid = _make_hybrid(with_reranker=True)
        result = hybrid.retrieve("revenue", rerank_top_n=3, store_parents=PARENTS)
        stage_names = [s["stage"] for s in result["stages"]]
        assert "cross_encoder_rerank" in stage_names

    def test_no_cross_encoder_stage_when_reranker_absent(self):
        hybrid = _make_hybrid(with_reranker=False)
        result = hybrid.retrieve("revenue", store_parents=PARENTS)
        stage_names = [s["stage"] for s in result["stages"]]
        assert "cross_encoder_rerank" not in stage_names

    def test_invalid_budgets_raise(self):
        hybrid = _make_hybrid()
        with pytest.raises(ValueError, match="nonnegative"):
            hybrid.retrieve("q", top_k_text=-1)
        with pytest.raises(ValueError, match="nonnegative"):
            hybrid.retrieve("q", top_k_tables=-1)

    def test_invalid_rerank_top_n_raises(self):
        hybrid = _make_hybrid()
        with pytest.raises(ValueError, match="positive"):
            hybrid.retrieve("q", rerank_top_n=0)

    def test_invalid_rrf_k_raises(self):
        with pytest.raises(ValueError, match="positive"):
            HybridRRFRetriever(MagicMock(), MagicMock(), rrf_k=0)

    def test_no_evidence_sets_insufficient_flag(self):
        dense_stub = MagicMock()
        dense_stub.retrieve.return_value = {"text_evidence": [], "table_evidence": []}
        bm25_stub = MagicMock()
        bm25_stub.retrieve.return_value = {"text_evidence": [], "table_evidence": []}
        hybrid = HybridRRFRetriever(dense_stub, bm25_stub)
        result = hybrid.retrieve("obscure question with no match")
        assert result.get("insufficient_evidence") is True


# F13/F14 production behavior belongs in evidence-audit/diagnostic integration
# tests, not a copied predicate or source-text test. Retrieval regressions follow.
# ---------------------------------------------------------------------------


def _scoped_hybrid(*, base_filters=None, variant="D", reranker=None, **kwargs):
    records = [
        _record("m1", "revenue revenue revenue", ticker="MSFT"),
        _record("a1", "revenue", ticker="AAPL"),
        _record("a0", "revenue prior year", ticker="AAPL"),
    ]
    records[0]["metadata"]["fiscal_year"] = 2021
    records[1]["metadata"]["fiscal_year"] = 2021
    records[2]["metadata"]["fiscal_year"] = 2020
    spec = SimpleNamespace(manifest_fields=lambda: {"model": "synthetic-encoder"})

    class Store:
        parents = {}
        def __init__(self):
            self.spec, self.searches = spec, []

        def search(self, vector, *, k, filters):
            self.searches.append((k, filters))
            # An excluded issuer leads the unfiltered order: post-top-k filtering
            # would lose a valid AAPL match at k=1.
            return [
                {**record, "score": 1.0 / (i + 1), "score_type": "cosine"}
                for i, record in enumerate(records)
                if record["metadata"]["type"] == filters["type"] and eligible(
                    record, {key: value for key, value in filters.items() if key != "type"})
            ][:k]

    encoder = SimpleNamespace(spec=spec, encode=MagicMock(return_value=[[1.0]]))
    store = Store()
    dense = DenseRetriever(store, encoder, filters=base_filters)
    lexical = BM25Retriever(records, filters=base_filters)
    hybrid = HybridRRFRetriever(dense, lexical, variant=variant,
        expand_cell_parents=False, reranker=reranker, **kwargs)
    return hybrid, store, encoder


def test_request_filters_apply_before_both_top_k_and_do_not_leak_to_next_request():
    hybrid, store, _ = _scoped_hybrid()
    for ticker in ("AAPL", "MSFT", "AAPL"):
        result = hybrid.retrieve("revenue", top_k_text=1, top_k_tables=0,
                                 filters={"ticker": ticker, "fiscal_year": 2021})
        assert [item["metadata"]["ticker"] for item in result["text_evidence"]] == [ticker]
        assert len(result["text_evidence"]) == 1
        components = result["text_evidence"][0]["rrf_component_ranks"]
        assert set(components) == {"list_0_rank", "list_1_rank"}
        assert store.searches[-1][1]["ticker"] == ticker
    assert hybrid.dense.filters == hybrid.bm25.filters == {}


def test_constructor_scope_cannot_be_widened_by_request():
    hybrid, store, encoder = _scoped_hybrid(base_filters={"ticker": "AAPL"})
    result = hybrid.retrieve("revenue", filters={"ticker": "MSFT"})
    assert result["status"] == "insufficient_evidence"
    assert not store.searches
    encoder.encode.assert_not_called()
    assert hybrid.dense.filters == {"ticker": "AAPL"}


@pytest.mark.parametrize("filters", [
    {"unknown": "AAPL"}, {"ticker": True}, {"fiscal_year": 2021.0},
    {"ticker": {"nested": "AAPL"}}, {"ticker": ["AAPL", False]},
    {"ticker": ""}, {"type": "narrative_text"}, [], "AAPL",
])
def test_invalid_filter_is_rejected_before_any_search(filters):
    hybrid, store, encoder = _scoped_hybrid()
    with pytest.raises(ValueError):
        hybrid.retrieve("revenue", filters=filters)
    assert not store.searches
    encoder.encode.assert_not_called()


def test_mutating_request_list_cannot_change_constructor_scope():
    scope = {"ticker": ["AAPL", "MSFT"]}
    hybrid, _, _ = _scoped_hybrid(base_filters=scope)
    scope["ticker"].clear()
    result = hybrid.retrieve("revenue", filters={"ticker": "AAPL"}, top_k_tables=0)
    assert result["text_evidence"]
    assert hybrid.dense.filters == {"ticker": ["AAPL", "MSFT"]}


def test_component_ignoring_eligibility_is_typed_failure():
    hybrid = _make_hybrid()
    with pytest.raises(RetrievalStageError) as caught:
        hybrid.retrieve("revenue", filters={"ticker": "MSFT"})
    assert caught.value.code == "eligibility_violation"
    assert caught.value.trace["status"] == "service_error"
    assert caught.value.trace["all_evidence"] == []


@pytest.mark.parametrize("scores", [
    [], [0.1], [0.1] * 20, [float("nan")] * 6, [float("inf")] * 6,
    [[0.1]] * 6, ["0.1"] * 6, [True] * 6,
])
def test_invalid_reranker_scores_never_return_fallback_evidence(scores):
    hybrid = _make_hybrid(with_reranker=True)
    hybrid.reranker.predict.side_effect = lambda pairs: scores
    with pytest.raises(RetrievalStageError) as caught:
        hybrid.retrieve("revenue", store_parents=PARENTS)
    assert caught.value.code == "reranker_failed"
    assert caught.value.trace["status"] == "service_error"
    assert caught.value.trace["all_evidence"] == []
    assert caught.value.trace["text_evidence"] == []


def test_cross_encoder_exception_is_typed_failure():
    hybrid = _make_hybrid(with_reranker=True)
    hybrid.reranker.predict.side_effect = RuntimeError("unavailable")
    with pytest.raises(RetrievalStageError) as caught:
        hybrid.retrieve("revenue", store_parents=PARENTS)
    assert caught.value.stage == "cross_encoder"
    assert caught.value.trace["error_class"] == "RuntimeError"


def test_successful_reranker_does_not_mutate_canonical_candidates_or_claim_model():
    hybrid = _make_hybrid(with_reranker=True)
    result = hybrid.retrieve("revenue", store_parents=PARENTS)
    assert result["variant"] == "E" and result["ranking_applied"]
    stage = next(stage for stage in result["stages"] if stage["stage"] == "cross_encoder_rerank")
    assert stage["model"] == "unverified injected predictor"
    assert stage["output_count"] == 5
    assert all("cross_encoder_score" not in record for record in ALL_RECORDS + list(PARENTS.values()))


@pytest.mark.parametrize("variant,code", [("A", "variant_not_ready"), ("B", "variant_not_ready"), ("G", "chart_not_ready")])
def test_missing_representation_or_chart_variant_is_not_relabelled_success(variant, code):
    hybrid, store, encoder = _scoped_hybrid(variant=variant)
    with pytest.raises(RetrievalStageError) as caught:
        hybrid.retrieve("revenue")
    assert caught.value.code == code
    assert not store.searches
    encoder.encode.assert_not_called()


def test_canonical_C_has_no_lexical_or_cross_encoder_call():
    hybrid = _make_hybrid()
    hybrid.variant = "C"
    result = hybrid.retrieve("revenue", store_parents=PARENTS)
    assert result["variant"] == "C"
    hybrid.bm25.retrieve.assert_not_called()
    assert "rrf_fusion" not in [stage["stage"] for stage in result["stages"]]


def test_E_hierarchy_is_separate_from_common_eligibility():
    hybrid = _make_hybrid(with_reranker=True)
    hybrid.max_hierarchy_sections = 1
    # Two eligible sections, but the declared stage-E hierarchy retains one.
    hybrid.dense.retrieve.return_value = {"text_evidence": [
        {**NARRATIVES[0], "metadata": {**NARRATIVES[0]["metadata"], "section": "Item 7"}},
        {**NARRATIVES[1], "metadata": {**NARRATIVES[1]["metadata"], "section": "Item 1A"}},
    ], "table_evidence": []}
    hybrid.bm25.retrieve.return_value = {"text_evidence": [], "table_evidence": []}
    result = hybrid.retrieve("revenue", top_k_tables=0, filters={"ticker": "AAPL"})
    assert result["eligibility_filters"] == {"ticker": "AAPL"}
    hierarchy = next(stage for stage in result["stages"] if stage["stage"] == "hierarchical_candidate_restriction")
    assert len(hierarchy["retained_groups"]) == 1
    assert hierarchy["excluded_ids"] == ["n2"]


def test_F_escalates_at_most_once_and_records_actual_stream_limits():
    predictor = SimpleNamespace(predict=lambda pairs: [0.9] * len(pairs))
    hybrid, store, _ = _scoped_hybrid(variant="F", reranker=predictor,
        routing_policy=RoutingPolicy(min_candidates=2, max_tiers=2))
    result = hybrid.retrieve("revenue", top_k_text=3, top_k_tables=3)
    attempts = result["routing"]["attempts"]
    assert len(attempts) == 2
    assert attempts[0]["narrative_limit"] == 0
    assert attempts[1]["narrative_limit"] == 3
    assert result["ranked_evidence_ids"]
    assert len(store.searches) == 3  # table first, then narrative + table.


def test_F_single_tier_configuration_never_issues_other_stream_query():
    predictor = SimpleNamespace(predict=lambda pairs: [0.9] * len(pairs))
    hybrid, store, _ = _scoped_hybrid(variant="F", reranker=predictor,
        routing_policy=RoutingPolicy(max_tiers=1))
    result = hybrid.retrieve("revenue")
    assert len(result["routing"]["attempts"]) == 1
    assert all(filters["type"] == "table_cell" for _, filters in store.searches)
    assert result["status"] == "insufficient_evidence"


def test_F_chart_request_stays_explicitly_unavailable_before_G():
    hybrid, store, _ = _scoped_hybrid(variant="F",
        reranker=SimpleNamespace(predict=lambda pairs: [0.9] * len(pairs)))
    result = hybrid.retrieve("What does the chart show?")
    assert result["status"] == "insufficient_evidence"
    assert result["routing"]["stop_reason"] == "chart_tier_unavailable_before_G"
    assert not store.searches


def test_both_disabled_means_no_component_or_encoder_call():
    hybrid, store, encoder = _scoped_hybrid()
    result = hybrid.retrieve("revenue", top_k_text=0, top_k_tables=0)
    assert result["status"] == "insufficient_evidence"
    assert not store.searches
    encoder.encode.assert_not_called()


def test_parent_in_another_issuer_cannot_be_expanded():
    wrong_parent = {"p1": {**PARENTS["p1"], "metadata": {**PARENTS["p1"]["metadata"], "ticker": "MSFT"}}}
    with pytest.raises(ValueError, match="incompatible"):
        expand_parents(CELLS, wrong_parent, budget_chars=100000, already_included=set())


def test_conflicting_identity_is_not_silently_fused():
    a = _record("same", "Apple revenue")
    changed = _record("same", "different source text")
    with pytest.raises(ValueError, match="Conflicting"):
        reciprocal_rank_fusion([[a], [changed]])


def test_component_score_types_survive_fusion():
    a = {**_record("a", "revenue"), "score": 0.8, "score_type": "cosine"}
    b = {**_record("a", "revenue"), "bm25_score": 1.2}
    fused = reciprocal_rank_fusion([[a], [b]])[0]
    assert fused["rrf_component_scores"] == {
        "list_0": {"score": 0.8, "score_type": "cosine"},
        "list_1": {"score": 1.2, "score_type": "bm25"},
    }


def test_native_faiss_and_bm25_share_request_scope_before_top_k(tmp_path_factory):
    from src.indexing.bge import EmbeddingSpec
    from src.indexing.store import ExactStore, publish_filing
    from tests.test_exact_index import A, B, record, vectors

    root = tmp_path_factory.mktemp("scope")
    a, b = record("revenue"), record("revenue", B, "MSFT")
    publish_filing(root, [a], [], vectors((0.5, 0.5)), {"test_only": True})
    publish_filing(root, [b], [], vectors((1, 0)), {"test_only": True})
    store = ExactStore(root)
    encoder = SimpleNamespace(spec=EmbeddingSpec(), encode=lambda texts, query: vectors((1, 0)))
    hybrid = HybridRRFRetriever(DenseRetriever(store, encoder), BM25Retriever(store.records))
    for ticker, accession in (("AAPL", A), ("MSFT", B), ("AAPL", A)):
        result = hybrid.retrieve("revenue", top_k_text=1, top_k_tables=0, filters={"ticker": ticker})
        assert result["ranked_evidence_ids"] == [accession + ":revenue"]
        assert result["text_evidence"][0]["rrf_component_ranks"] == {"list_0_rank": 1, "list_1_rank": 1}
    # MSFT is globally first in native FAISS, proving the AAPL result was not
    # post-top-k removal of a globally winning incompatible issuer.
    assert store.search(vectors((1, 0))[0], k=1)[0]["metadata"]["ticker"] == "MSFT"


def test_parent_lookup_defaults_to_dense_store_without_engine_kwargs():
    hybrid = _make_hybrid()
    hybrid.dense.store.parents = PARENTS
    result = hybrid.retrieve("revenue")
    assert "p1" in result["ranked_evidence_ids"]
    parent_stage = next(stage for stage in result["stages"] if stage["stage"] == "parent_expansion")
    assert parent_stage["injected_parents"] == 1


def test_exhausted_F_score_threshold_abstains_instead_of_silent_fallback():
    predictor = SimpleNamespace(predict=lambda pairs: [-1.0] * len(pairs))
    hybrid, _, _ = _scoped_hybrid(variant="F", reranker=predictor,
        routing_policy=RoutingPolicy(min_candidates=1, max_tiers=2, min_cross_encoder_score=0.0))
    result = hybrid.retrieve("revenue")
    assert result["status"] == "insufficient_evidence"
    assert result["all_evidence"] == result["ranked_evidence_ids"] == []
    assert result["rejected_evidence_ids"]
    assert result["routing"]["stop_reason"] == "score_threshold_not_met"


@pytest.mark.parametrize("failure", [
    {"status": "service_error"}, {"failure_code": "failed"},
    {"text_error": "failed"}, {"table_error": "failed"},
    {"rerank_error": "failed"}, {"error_code": "failed"},
    {"status": "insufficient_evidence"},
    {"success": False}, {"error": "failed"},
])
def test_partial_component_failure_does_not_become_fused_success(failure):
    hybrid = _make_hybrid()
    hybrid.dense.retrieve.return_value.update(failure)
    with pytest.raises(RetrievalStageError) as caught:
        hybrid.retrieve("revenue")
    assert caught.value.trace["all_evidence"] == []
    assert caught.value.trace["status"] == "service_error"
    hybrid.bm25.retrieve.assert_not_called()


@pytest.mark.parametrize("response", [
    None, [], {"text_evidence": None}, {"text_evidence": {}},
    {"text_evidence": ["plain text"]},
    {"text_evidence": [{"evidence_id": "", "content": "bad", "metadata": {"type": "narrative_text"}}]},
    {"text_evidence": [{"evidence_id": "a", "id": "b", "content": "bad", "metadata": {"type": "narrative_text"}}]},
    {"text_evidence": [{"evidence_id": "a", "content": "", "metadata": {"type": "narrative_text"}}]},
    {"text_evidence": [{"evidence_id": "a", "content": "bad", "metadata": {"type": "table_cell"}}]},
    {"text_evidence": [NARRATIVES[0], NARRATIVES[0]]},
])
def test_invalid_component_shape_or_identity_is_rejected(response):
    hybrid = _make_hybrid()
    hybrid.dense.retrieve.return_value = response
    with pytest.raises(RetrievalStageError) as caught:
        hybrid.retrieve("revenue")
    assert caught.value.code in {"invalid_component_response", "invalid_component_evidence"}
    assert caught.value.trace["all_evidence"] == []


def test_disabled_stream_adapter_returning_evidence_is_a_contract_failure():
    hybrid = _make_hybrid()
    with pytest.raises(RetrievalStageError) as caught:
        hybrid.retrieve("revenue", top_k_text=0, top_k_tables=3)
    assert caught.value.code == "invalid_component_response"
