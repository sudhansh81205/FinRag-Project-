"""Reproductions for source identity and candidate loss; synthetic data only."""

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.retrieval.bm25 import (
    HybridRRFRetriever,
    RoutingPolicy,
    expand_parents,
    reciprocal_rank_fusion,
)
from tests.test_generation import engine_with, real_stub
from tests.test_pavan_retrieval import CELLS, NARRATIVES, PARENTS


def test_fusion_rejects_different_original_sources_for_one_id():
    left = {**deepcopy(NARRATIVES[0]), "source": {"page": 1, "sha256": "a" * 64}}
    right = {**deepcopy(left), "source": {"page": 2, "sha256": "b" * 64}}
    with pytest.raises(ValueError, match="source"):
        reciprocal_rank_fusion([[left], [right]])
    assert reciprocal_rank_fusion([[left], [deepcopy(left)]])[0]["source"] == left["source"]


def test_parent_allowance_cannot_discard_primary_retrieved_cells():
    for allowance in (0, len(PARENTS["p1"]["content"]) + 20):
        expanded = expand_parents(CELLS, PARENTS, budget_chars=allowance, already_included=set())
        assert [item["evidence_id"] for item in expanded if item["metadata"]["type"] == "table_cell"] == ["c1", "c2"]


def test_primary_candidates_stay_ahead_of_optional_parent_context():
    expanded = expand_parents(CELLS, PARENTS, budget_chars=10000, already_included=set())
    assert [item["evidence_id"] for item in expanded] == ["c1", "c2", "p1"]


def test_five_passage_limit_keeps_five_primary_cells_before_parents():
    cells, parents = [], {}
    for i in range(5):
        cell, parent = deepcopy(CELLS[0]), deepcopy(PARENTS["p1"])
        cell["evidence_id"] = f"cell-{i}"
        cell["metadata"]["parent_table_id"] = f"parent-{i}"
        parent["evidence_id"] = f"parent-{i}"
        cells.append(cell)
        parents[parent["evidence_id"]] = parent
    expanded = expand_parents(cells, parents, budget_chars=10000, already_included=set())
    engine = engine_with([], real_stub())
    engine.retriever.retrieve.return_value = {"all_evidence": expanded, "ranking_applied": True}
    result = engine.answer_financial_question("source amounts")
    assert result["status"] == "ok"
    assert result["included_evidence_ids"] == [cell["evidence_id"] for cell in cells]
    assert [entry["reason"] for entry in result["excluded_evidence"]] == ["passage_limit"] * 5


def test_route_exhaustion_does_not_accept_candidate_count_below_policy():
    response = {"text_evidence": NARRATIVES[:1], "table_evidence": []}
    dense = SimpleNamespace(filters={}, retrieve=Mock(return_value=response))
    lexical = SimpleNamespace(filters={}, retrieve=Mock(return_value=response))
    hybrid = HybridRRFRetriever(dense, lexical, variant="F", expand_cell_parents=False,
        reranker=Mock(predict=Mock(return_value=[2.0])),
        routing_policy=RoutingPolicy(min_candidates=3, max_tiers=1))
    result = hybrid.retrieve("risk factors", top_k_text=3, top_k_tables=0)
    assert result["status"] == "insufficient_evidence"
    assert result["all_evidence"] == []
    assert result["routing"]["stop_reason"] == "candidate_threshold_not_met"
    assert result["rejected_evidence_ids"] == ["n1"]
    hybrid.routing_policy = RoutingPolicy(min_candidates=1, max_tiers=1)
    assert hybrid.retrieve("risk factors", top_k_text=3, top_k_tables=0)["status"] == "ok"
