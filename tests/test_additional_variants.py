"""Injected approval fixtures exercise contracts; they are never real human reviews."""
import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from src.charts.approval import caption_fingerprint, load_reviewed_captions
from src.retrieval.cross_encoder import verify_assets
from src.retrieval.variants import ApprovedChartPool, ChartTierRetriever, RepresentationRetriever

ROOT = Path(__file__).resolve().parents[1]


def test_representation_adapter_rejects_cells_and_wrong_narrative_policy():
    dense = SimpleNamespace(table_kind="table_cell", store=SimpleNamespace(records=[{}], parents={}))
    with pytest.raises(ValueError, match="flattened"):
        RepresentationRetriever(dense, "A")
    dense.table_kind = "financial_table"
    dense.store.records = [{"evidence_id": "source:fixed:0:100", "metadata": {"type": "narrative_text"}}]
    with pytest.raises(ValueError, match="Narrative"):
        RepresentationRetriever(dense, "B")
    dense.retrieve = lambda *_args, **_kwargs: {"text_evidence": [], "table_evidence": []}
    retriever = RepresentationRetriever(dense, "A")
    assert retriever.retrieve("Question", top_k_text=0, top_k_tables=0)["status"] == "insufficient_evidence"


def test_caption_approval_is_separate_from_question_approval(tmp_path):
    path = ROOT / "docs/reports/2026-11-09-chart-set/captions/candidate-captions.json"
    captions = json.loads(path.read_text())
    marks = {"reviewer_identity": "test-fixture-reviewer", "reviewed_at": "2026-01-01T00:00:00Z",
             "method": "human_original_image_and_source",
             "caption_reviews": [{"evidence_id": item["evidence_id"],
                "caption_sha256": caption_fingerprint(item), "image_sha256": item["metadata"]["image_sha256"],
                "decision": "passed", "original_image_checked": True,
                "source_provenance_checked": True, "basis": "Injected approval fixture only"} for item in captions]}
    review = tmp_path / "review.json"
    review.write_text(json.dumps(marks))
    def load(authors=("test-fixture-author",)):
        return load_reviewed_captions(path, review, ROOT / "data/charts",
            trusted_reviewers=["test-fixture-reviewer"], caption_authors=authors)
    approved = load()
    assert len(approved) == 6 and all(item["metadata"]["independent_review"] == "passed" for item in approved)
    assert all(hashlib.sha256(item["content"].encode()).hexdigest() == item["metadata"]["content_sha256"] for item in approved)
    assert all(item["status"] == "candidate" for item in json.loads(path.read_text()))
    with pytest.raises(ValueError, match="independent"):
        load(authors=("test-fixture-reviewer",))
    marks["caption_reviews"][0]["caption_sha256"] = "0" * 64
    review.write_text(json.dumps(marks))
    with pytest.raises(ValueError, match="stale"):
        load()
    marks["caption_reviews"] = []
    review.write_text(json.dumps(marks))
    with pytest.raises(ValueError, match="Every caption"):
        load()


def test_chart_pool_filters_before_embedding_and_never_accepts_pending():
    class Encoder:
        calls = 0
        def encode(self, texts, **_kwargs):
            self.calls += 1
            return np.ones((len(texts), 768), dtype=np.float32)
    encoder = Encoder()
    record = {"status": "approved", "evidence_id": "fixture:chart", "content": "Printed title: stock return chart",
              "metadata": {"type": "chart_description", "independent_review": "passed", "ticker": "AAPL",
                           "accession": "fixture-filing", "image_sha256": "a" * 64},
              "source": {"source_asset_id": "fixture:source", "image_sha256": "a" * 64},
              "review": {"approval_sha256": "b" * 64}}
    record["metadata"]["content_sha256"] = hashlib.sha256(record["content"].encode()).hexdigest()
    pool = ApprovedChartPool([record], encoder)
    before = encoder.calls
    assert pool.retrieve("stock return", filters={"ticker": "MSFT"}) == []
    assert pool.retrieve("stock return", k=0) == []
    assert encoder.calls == before
    found = pool.retrieve("stock return", filters={"ticker": "AAPL"})
    assert len(found) == 1 and found[0]["evidence_id"] == "fixture:chart"
    changed = copy.deepcopy(record)
    changed["metadata"]["independent_review"] = "pending"
    with pytest.raises(ValueError, match="unreviewed"):
        ApprovedChartPool([changed], encoder)


def test_chart_only_and_disabled_chart_streams_do_not_query_text_or_tables():
    class Base:
        variant = "F"
        reranker = object()
        dense = SimpleNamespace(filters={})
        bm25 = SimpleNamespace(filters={})
        def retrieve(self, *_args, **_kwargs):
            raise AssertionError("A chart-only request cannot query text/table streams")
        def _rerank(self, _query, candidates, _limit, result):
            result["stages"].append({"stage": "cross_encoder_rerank"})
            return candidates
    class Pool:
        calls = 0
        def retrieve(self, *_args, **_kwargs):
            self.calls += 1
            return []
    pool = Pool()
    retriever = ChartTierRetriever(Base(), pool)
    assert retriever.retrieve("A chart question", chart_only=True)["status"] == "insufficient_evidence"
    assert pool.calls == 1
    assert retriever.retrieve("A chart question", routing={"chart": False})["status"] == "insufficient_evidence"
    assert pool.calls == 1


def test_cross_encoder_missing_assets_refuse_before_loading_transformers(tmp_path):
    with pytest.raises(ValueError, match="pinned"):
        verify_assets(tmp_path)
