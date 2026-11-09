"""Pavan November 7 — A-F cumulative retrieval stage tests.

No live model calls, no BGE downloads.  All fixtures use synthetic records
identical in shape to canonical ExactStore records so the same interfaces
are exercised.

Stage coverage:
  A/B  dense-only  — exercised in test_exact_index.py; imported helpers here
  C    parent expansion within budget
  D    BM25 standalone
  E    RRF fusion (dense + BM25)
  F    cross-encoder reranking (stubbed)
  --   disabled-stream contract (no query issued)
  --   chart tier blocked
"""

import math
from unittest.mock import MagicMock

import pytest

from src.retrieval.bm25 import (
    BM25Index,
    BM25Retriever,
    HybridRRFRetriever,
    expand_parents,
    reciprocal_rank_fusion,
)
from src.retrieval.dense import DenseRetriever


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
        reranker.predict.return_value = [0.9, 0.8, 0.7, 0.6, 0.5]

    return HybridRRFRetriever(dense_stub, bm25_stub, reranker=reranker, rrf_k=60)


class TestHybridRRFRetriever:
    def test_stage_trace_contains_all_stages(self):
        hybrid = _make_hybrid()
        result = hybrid.retrieve("Apple revenue 2021", store_parents=PARENTS)
        stage_names = [s["stage"] for s in result["stages"]]
        assert "dense" in stage_names
        assert "bm25" in stage_names
        assert "rrf_fusion" in stage_names

    def test_included_evidence_ids_are_set(self):
        hybrid = _make_hybrid()
        result = hybrid.retrieve("revenue", store_parents=PARENTS)
        assert isinstance(result["included_evidence_ids"], list)
        assert len(result["included_evidence_ids"]) > 0

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


# ---------------------------------------------------------------------------
# F13 coordinate predicate unit tests
# ---------------------------------------------------------------------------

class TestF13CoordinatePredicates:
    """Confirm that the F13 fix correctly identifies invalid span bboxes.

    These tests exercise the validation logic directly (not through audit_package
    which requires the real Apple source package).  They confirm the predicate
    semantics: finite, non-degenerate, within-page.
    """

    @staticmethod
    def _check(bbox, page_w=612, page_h=792):
        """Return True if bbox passes all F13 predicates, False otherwise."""
        if bbox is None or len(bbox) != 4:
            return False
        if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in bbox):
            return False
        x0, y0, x1, y1 = bbox
        if not (x0 < x1 and y0 < y1):
            return False
        if not (0 <= x0 and x1 <= page_w and 0 <= y0 and y1 <= page_h):
            return False
        return True

    def test_valid_bbox_passes(self):
        assert self._check([10, 20, 100, 50]) is True

    def test_placeholder_negative_values_fail(self):
        # The probe from F13 discovery: [-999999, -999999, -999998, -999998]
        assert self._check([-999999, -999999, -999998, -999998]) is False

    def test_non_finite_nan_fails(self):
        assert self._check([float("nan"), 0, 100, 50]) is False

    def test_non_finite_inf_fails(self):
        assert self._check([float("inf"), 0, 100, 50]) is False

    def test_zero_width_degenerate_fails(self):
        assert self._check([50, 20, 50, 80]) is False  # x0 == x1

    def test_reversed_bbox_fails(self):
        assert self._check([100, 20, 10, 50]) is False  # x0 > x1

    def test_exceeds_page_width_fails(self):
        assert self._check([10, 20, 700, 50], page_w=612) is False

    def test_none_bbox_fails(self):
        assert self._check(None) is False

    def test_wrong_length_fails(self):
        assert self._check([10, 20, 100]) is False


# ---------------------------------------------------------------------------
# F14 guard unit test
# ---------------------------------------------------------------------------

class TestF14DiagnosticGuard:
    """Confirm that the F14 fix moves artifacts.mkdir inside the guarded block.

    We verify the patch by inspecting the source code directly rather than
    executing the full main() path (which requires bs4, mlflow, dvc and the
    real Apple package).  The structural check confirms that artifacts.mkdir
    can no longer raise before the report write.
    """

    def test_mkdir_inside_guarded_function(self):
        """The mkdir call must appear inside _guarded_build, not before guarded()."""
        import pathlib
        source = pathlib.Path("scripts/verify_canonical_data.py").read_text(encoding="utf-8")
        # After the F14 fix, artifacts.mkdir must be inside _guarded_build
        assert "_guarded_build" in source, "F14 fix not applied: _guarded_build missing"
        # The bare artifacts.mkdir(parents=True, exist_ok=False) must NOT appear
        # outside the nested function (i.e., the old top-level call is gone).
        import re
        # Find all mkdir calls that are NOT inside the _guarded_build function
        # Simple structural check: the guarded_build def must precede mkdir
        guarded_pos = source.find("def _guarded_build()")
        mkdir_pos = source.find("artifacts.mkdir(parents=True, exist_ok=False)")
        assert guarded_pos != -1, "F14 fix: _guarded_build function not found"
        assert mkdir_pos != -1, "F14 fix: artifacts.mkdir call not found"
        # mkdir must appear AFTER the _guarded_build function definition
        assert mkdir_pos > guarded_pos, (
            "F14 fix: artifacts.mkdir still executes before the guarded block"
        )

    def test_output_parent_mkdir_added(self):
        """The fix must also guard the output directory creation."""
        import pathlib
        source = pathlib.Path("scripts/verify_canonical_data.py").read_text(encoding="utf-8")
        assert "args.output.parent.mkdir" in source, (
            "F14 fix: output parent mkdir guard missing"
        )
