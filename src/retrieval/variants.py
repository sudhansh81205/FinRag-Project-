"""Representation-specific A/B retrieval and the independently approved G tier.

The default C/D runtime does not activate these adapters. Real local indexes,
identified cross-encoding and accepted original-image captions are explicit inputs.
"""
import copy
import hashlib
import re

from src.retrieval.bm25 import BM25Index, reciprocal_rank_fusion
from src.retrieval.eligibility import eligible, intersect_filters, validated_filters


class RepresentationRetriever:
    def __init__(self, dense, variant):
        if variant not in {"A", "B"} or dense.table_kind != "financial_table":
            raise ValueError("A/B require their own flattened-table dense index")
        records = dense.store.records
        if not records or dense.store.parents:
            raise ValueError("A/B cannot use the C cell/parent representation")
        for record in records:
            kind = record["metadata"].get("type")
            if kind == "financial_table":
                if not record["metadata"].get("source_evidence_ids"):
                    raise ValueError("Flattened tables must retain source cell identities")
            elif kind == "narrative_text":
                fixed = ":fixed:" in record["evidence_id"]
                if fixed != (variant == "A"):
                    raise ValueError("Narrative representation does not match A/B")
            else:
                raise ValueError("A/B cannot silently include cell or chart candidates")
        self.dense, self.variant, self.reranker = dense, variant, None

    def retrieve(self, query, top_k_text=5, top_k_tables=5, *, filters=None):
        result = self.dense.retrieve(query, top_k_text, top_k_tables, filters=filters)
        ranked = result.get("all_evidence", [])
        return {**result, "variant": self.variant,
                "status": "ok" if ranked else "insufficient_evidence", "ranking_applied": True,
                "all_evidence": ranked, "ranked_evidence_ids": [item["evidence_id"] for item in ranked],
                "candidate_evidence_ids": [item["evidence_id"] for item in ranked],
                "stages": [{"stage": "representation_index", "variant": self.variant,
                            "tables": "flattened_markdown", "narratives": "fixed_overlap" if self.variant == "A" else "section_aware"},
                           {"stage": "dense", "text_count": len(result["text_evidence"]),
                            "table_count": len(result["table_evidence"])}]}


class ApprovedChartPool:
    """An exact FAISS/BM25 pool over verified, independently reviewed captions."""

    def __init__(self, captions, encoder):
        import faiss

        from src.indexing.bge import DIMENSION, unit_vectors
        if not captions or len({item.get("evidence_id") for item in captions}) != len(captions):
            raise ValueError("G requires unique approved chart evidence")
        for item in captions:
            meta = item.get("metadata", {})
            source = item.get("source", {})
            if (item.get("status") != "approved" or meta.get("independent_review") != "passed"
                    or not item.get("review", {}).get("approval_sha256")
                    or meta.get("image_sha256") != source.get("image_sha256")
                    or hashlib.sha256(item["content"].encode()).hexdigest() != meta.get("content_sha256")):
                raise ValueError("G cannot index unreviewed or changed captions")
        self.records, self.encoder = copy.deepcopy(captions), encoder
        self.vectors = unit_vectors(encoder.encode([item["content"] for item in captions]), len(captions))
        self.index = faiss.IndexFlatIP(DIMENSION)
        self.index.add(self.vectors)
        self.lexical = BM25Index(self.records)

    def retrieve(self, query, *, k=5, filters=None, asset_id=None):
        import faiss

        from src.indexing.bge import DIMENSION, unit_vectors
        if type(k) is not int or k < 0:
            raise ValueError("Chart retrieval limit must be a nonnegative integer")
        filters = validated_filters(filters)
        rows = [index for index, item in enumerate(self.records) if eligible(item, filters)
                and (asset_id is None or asset_id in {item["source"]["source_asset_id"], item["source"]["image_sha256"]})]
        if not k or not rows:
            return []  # disabled streams make no embedding or lexical call
        index = faiss.IndexFlatIP(DIMENSION)
        index.add(self.vectors[rows])
        vector = unit_vectors(self.encoder.encode([query], query=True), 1)
        scores, indices = index.search(vector, min(k, len(rows)))
        dense = [{**copy.deepcopy(self.records[rows[row]]), "score": float(score), "dense_rank": rank}
                 for rank, (row, score) in enumerate(zip(indices[0], scores[0], strict=True), 1)]
        # Restrict before lexical top-k as well, including an explicit selected original asset.
        lexical = BM25Index([self.records[row] for row in rows]).search(query, k=k)
        return reciprocal_rank_fusion([dense, lexical], k=60)


class ChartTierRetriever:
    def __init__(self, base, pool):
        if base.variant != "F" or base.reranker is None:
            raise ValueError("G extends the real F routing/cross-encoder adapter")
        self.base, self.pool, self.variant = base, pool, "G"
        self.dense, self.reranker = base.dense, base.reranker

    def retrieve(self, query, top_k_text=5, top_k_tables=5, *, filters=None, routing=None,
                 chart_only=False, chart_asset_id=None):
        if not isinstance(query, str) or not query.strip():
            raise ValueError("A chart request needs a question")
        routing = {} if routing is None else routing
        if (not isinstance(routing, dict) or set(routing) - {"narrative", "table", "chart"}
                or any(type(value) is not bool for value in routing.values())):
            raise ValueError("Invalid chart routing switches")
        chart_question = chart_only or bool(re.search(r"\b(chart|graph|plot|shareholder|stock|axis|axes)\b", query, re.I))
        if chart_question:
            result = {"status": "insufficient_evidence", "all_evidence": [], "stages": [],
                      "routing": {"attempts": [], "question_kind": "chart"}, "ranking_applied": True}
        else:
            result = self.base.retrieve(query, top_k_text, top_k_tables, filters=filters,
                                       routing={key: value for key, value in routing.items() if key != "chart"})
        result.update(variant="G", chart_evidence=[], retrieval_mode="routed_approved_charts")
        result["routing"].update(chart=False, chart_blocked_reason=None)
        if not routing.get("chart", True) or not (chart_question or result["status"] != "ok"):
            return result
        scope = intersect_filters(self.base.dense.filters, self.base.bm25.filters, filters)
        charts = self.pool.retrieve(query, k=5, filters=scope, asset_id=chart_asset_id)
        result["stages"].append({"stage": "approved_chart_evidence", "variant": "G", "count": len(charts),
                                 "image_sha256": [item["metadata"]["image_sha256"] for item in charts]})
        result["routing"]["chart"] = True
        candidates = result.get("all_evidence", []) + charts
        result["candidate_evidence_ids"] = [item["evidence_id"] for item in candidates]
        ranked = self.base._rerank(query, candidates, 5, result)
        result.update(all_evidence=ranked, ranked_evidence_ids=[item["evidence_id"] for item in ranked],
                      chart_evidence=[item for item in ranked if item["metadata"]["type"] == "chart_description"],
                      text_evidence=[item for item in ranked if item["metadata"]["type"] == "narrative_text"],
                      table_evidence=[item for item in ranked if item["metadata"]["type"] in {"table_cell", "financial_table"}],
                      status="ok" if ranked else "insufficient_evidence")
        result["routing"]["attempts"].append({"tier": "approved_chart", "ranked_ids": result["ranked_evidence_ids"],
                                               "stop_reason": "source_bound_charts" if ranked else "no_eligible_chart"})
        return result
