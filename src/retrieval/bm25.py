"""BM25 retriever and Reciprocal Rank Fusion (RRF) hybrid for FinRAG.

Pavan's November 7 task: implement A-F cumulative retrieval stages.

BM25 provides lexical/exact-term matching over the same canonical candidate
set used by the dense index. RRF combines dense and BM25 rankings without
needing score calibration.  The chart tier (stage G) remains disabled until
accepted chart descriptions exist.

Canonical mapping: A fixed-overlap narrative/flattened tables; B section-aware
chunks; C self-describing cells/parents; D BM25/dense RRF60; E hierarchical
restriction plus cross-encoding; F bounded routing; G approved chart evidence.
A/B need their own representation-specific indexes: filtering sections on a C
index does not implement those controls. This adapter exposes C-F components,
and rejects unavailable A/B/G instead of relabelling a different experiment.
"""

import math
import re
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
from numbers import Real
from typing import Any

from .dense import DenseRetriever
from .eligibility import eligible, empty_scope, intersect_filters, validated_filters

# ---------------------------------------------------------------------------
# Tokenizer: simple whitespace/punctuation split, lowercase
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


# ---------------------------------------------------------------------------
# BM25 implementation (Okapi BM25, no external dependency)
# ---------------------------------------------------------------------------

class BM25Index:
    """Okapi BM25 index over a list of canonical evidence records.

    Records must each have an ``evidence_id`` string and a ``content`` string.
    Parameters follow the standard defaults: k1=1.5, b=0.75.
    """

    def __init__(self, records: list[dict[str, Any]], *, k1: float = 1.5, b: float = 0.75):
        if not records:
            raise ValueError("BM25Index requires at least one record")
        if not (isinstance(k1, Real) and not isinstance(k1, bool) and math.isfinite(k1) and k1 > 0):
            raise ValueError("BM25 k1 must be finite and positive")
        if not (isinstance(b, Real) and not isinstance(b, bool) and math.isfinite(b) and 0 <= b <= 1):
            raise ValueError("BM25 b must be finite and between zero and one")
        ids = [r.get("evidence_id") for r in records]
        if any(not isinstance(eid, str) or not eid.strip() for eid in ids) or len(ids) != len(set(ids)):
            raise ValueError("BM25 requires unique canonical evidence IDs")
        if any(not isinstance(r.get("content"), str) or not isinstance(r.get("metadata"), dict) for r in records):
            raise ValueError("BM25 requires content and canonical metadata")
        self.records = deepcopy(records)
        self.k1 = k1
        self.b = b
        # Build inverted index
        self._doc_tokens: list[list[str]] = []
        self._doc_len: list[int] = []
        self._df: dict[str, int] = defaultdict(int)
        for record in records:
            tokens = _tokenize(record["content"])
            self._doc_tokens.append(tokens)
            self._doc_len.append(len(tokens))
            for term in set(tokens):
                self._df[term] += 1
        self._N = len(records)
        self._avgdl = sum(self._doc_len) / self._N

    def _idf(self, term: str) -> float:
        df = self._df.get(term, 0)
        if df == 0:
            return 0.0
        return math.log((self._N - df + 0.5) / (df + 0.5) + 1)

    def score(self, query: str, doc_index: int) -> float:
        """Return BM25 score for one document."""
        query_terms = _tokenize(query)
        tokens = self._doc_tokens[doc_index]
        dl = self._doc_len[doc_index]
        tf_map: dict[str, int] = defaultdict(int)
        for t in tokens:
            tf_map[t] += 1
        total = 0.0
        denom = dl / self._avgdl if self._avgdl > 0 else 1.0
        for term in set(query_terms):
            tf = tf_map.get(term, 0)
            if tf == 0:
                continue
            idf = self._idf(term)
            tf_norm = (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * denom))
            total += idf * tf_norm
        return total

    def search(self, query: str, *, k: int = 10, filters: dict | None = None) -> list[dict[str, Any]]:
        """Return up to *k* records ranked by BM25, applying eligibility filters first.

        Filters follow the same key/value convention as ``ExactStore.search``:
        a list value means "any of".  Disabled (k=0) returns an empty list
        without computing any scores.
        """
        if type(k) is not int or k < 0:
            raise ValueError("k must be a nonnegative integer")
        filters = validated_filters(filters)
        if k == 0 or empty_scope(filters):
            return []
        eligible_rows = [
            i for i, record in enumerate(self.records)
            if eligible(record, filters)
        ]
        if not eligible_rows:
            return []
        scored = sorted(
            ((self.score(query, i), i) for i in eligible_rows),
            key=lambda pair: (-pair[0], self.records[pair[1]]["evidence_id"]),
        )[:k]
        return [
            {
                **deepcopy(self.records[row]),
                "bm25_score": score,
                "bm25_rank": rank,
                "eligible_count": len(eligible_rows),
            }
            for rank, (score, row) in enumerate(scored, 1) if score > 0
        ]


# ---------------------------------------------------------------------------
# BM25Retriever: lexical component of canonical stage D, or diagnostic alone
# ---------------------------------------------------------------------------

class BM25Retriever:
    """Lexical retrieval over the same canonical records as the dense index.

    *records* is ``ExactStore.records`` (a list of canonical dicts).
    ``retrieve`` returns the same dict shape as ``DenseRetriever.retrieve``
    so callers can substitute either adapter without branching.
    """

    def __init__(self, records: list[dict[str, Any]], *, filters: dict | None = None):
        if not records:
            raise ValueError("BM25Retriever requires at least one record")
        self.records = records
        self.filters = validated_filters(filters)
        # Build one index per stream type, populated lazily.
        self._narrative_records = [r for r in records if r["metadata"].get("type") == "narrative_text"]
        self._cell_records = [r for r in records if r["metadata"].get("type") == "table_cell"]
        self._narrative_index: BM25Index | None = (
            BM25Index(self._narrative_records) if self._narrative_records else None
        )
        self._cell_index: BM25Index | None = (
            BM25Index(self._cell_records) if self._cell_records else None
        )

    def retrieve(self, query: str, top_k_text: int = 3, top_k_tables: int = 3, *, filters=None) -> dict[str, Any]:
        if any(type(k) is not int or k < 0 for k in (top_k_text, top_k_tables)):
            raise ValueError("Retrieval budgets must be nonnegative integers")
        scope = intersect_filters(self.filters, filters)
        result: dict[str, Any] = {
            "query": query,
            "text_evidence": [],
            "table_evidence": [],
            "retrieval_mode": "bm25_only",
            "eligibility_filters": scope,
        }
        if not (top_k_text or top_k_tables) or empty_scope(scope):
            return result
        if top_k_text and self._narrative_index is not None:
            result["text_evidence"] = self._narrative_index.search(
                query, k=top_k_text, filters=scope
            )
        if top_k_tables and self._cell_index is not None:
            result["table_evidence"] = self._cell_index.search(
                query, k=top_k_tables, filters=scope
            )
        return result


# ---------------------------------------------------------------------------
# Reciprocal Rank Fusion (RRF k=60)
# ---------------------------------------------------------------------------

def reciprocal_rank_fusion(
    ranked_lists: list[list[dict[str, Any]]],
    *,
    k: int = 60,
    id_key: str = "evidence_id",
) -> list[dict[str, Any]]:
    """Fuse multiple ranked lists with RRF.

    Each item in each list must have ``id_key`` (evidence_id).  The fused list
    preserves all component ranks and the final RRF score in the returned dicts.
    Ties are broken deterministically by evidence_id ascending.

    ``k`` is the RRF constant (default 60 as specified in the PRD).
    """
    if type(k) is not int or k <= 0:
        raise ValueError("RRF constant k must be positive")
    rrf_scores: dict[str, float] = defaultdict(float)
    component_ranks: dict[str, dict[str, int]] = defaultdict(dict)
    component_scores: dict[str, dict[str, Any]] = defaultdict(dict)
    # Map evidence_id -> canonical record (first occurrence wins)
    id_to_item: dict[str, dict[str, Any]] = {}
    for list_index, ranked in enumerate(ranked_lists):
        seen = set()
        for rank, item in enumerate(ranked, 1):
            eid = item.get(id_key) or item.get("id")
            if not isinstance(eid, str) or not eid.strip():
                continue
            if eid in seen:
                raise ValueError("Duplicate evidence identity in a ranking")
            seen.add(eid)
            if eid in id_to_item and any(item.get(key) != id_to_item[eid].get(key) for key in ("content", "metadata", "source")):
                raise ValueError("Conflicting content, metadata or source for evidence identity")
            rrf_scores[eid] += 1.0 / (k + rank)
            component_ranks[eid][f"list_{list_index}_rank"] = rank
            component_scores[eid][f"list_{list_index}"] = {
                "score": item.get("score", item.get("bm25_score")),
                "score_type": item.get("score_type", "bm25" if "bm25_score" in item else "unspecified"),
            }
            if eid not in id_to_item:
                id_to_item[eid] = deepcopy(item)
    fused = sorted(
        rrf_scores.items(),
        key=lambda pair: (-pair[1], pair[0]),
    )
    return [
        {
            **id_to_item[eid],
            "evidence_id": eid,
            "rrf_score": score,
            "rrf_component_ranks": component_ranks[eid],
            "rrf_component_scores": component_scores[eid],
        }
        for eid, score in fused
    ]


# ---------------------------------------------------------------------------
# Parent expansion helper (stage C)
# ---------------------------------------------------------------------------

def expand_parents(
    candidates: list[dict[str, Any]],
    store_parents: dict[str, dict[str, Any]],
    *,
    budget_chars: int,
    already_included: set[str],
) -> list[dict[str, Any]]:
    """Append optional parent context without discarding primary candidates.

    For each ``table_cell`` candidate whose parent has not yet been included,
    append the parent record if it fits in the parent allowance. Primary evidence
    keeps its rank and is never dropped by this expansion-only limit. The engine
    alone applies the common final context budget and records excluded IDs.

    Returns a new list that may contain parent records appended after their
    child cells.  Candidates that have no parent in ``store_parents`` are
    passed through unchanged.

    This implements stage C parent expansion.  The caller is responsible for
    deduplication and final token-budget enforcement.
    """
    if type(budget_chars) is not int or budget_chars < 0:
        raise ValueError("Parent budget must be a nonnegative integer")
    expanded: list[dict[str, Any]] = list(candidates)
    candidate_ids = {_identity(item) for item in candidates}
    used_chars = [0]  # mutable surrogate for nonlocal

    def fits(item: dict[str, Any]) -> bool:
        cost = len(item.get("content", "")) + 20  # slack for ID prefix
        if used_chars[0] + cost > budget_chars:
            return False
        used_chars[0] += cost
        return True

    for candidate in candidates:
        kind = candidate.get("metadata", {}).get("type")
        if kind == "table_cell":
            parent_id = candidate.get("metadata", {}).get("parent_table_id")
            if parent_id and parent_id not in already_included and parent_id not in candidate_ids:
                parent = store_parents.get(parent_id)
                if parent is not None:
                    if parent.get("evidence_id", parent.get("id")) != parent_id:
                        raise ValueError("Parent identity does not match its lookup key")
                    if any(parent.get("metadata", {}).get(key) != candidate["metadata"].get(key) for key in ("ticker", "accession")):
                        raise ValueError("Parent and cell have incompatible source identity")
                if parent is not None and fits(parent):
                    already_included.add(parent_id)
                    expanded.append({**parent, "expansion": "parent_of_cell"})
    return expanded


# ---------------------------------------------------------------------------
# Canonical C-F retrieval components with explicit unavailable-variant gates
# ---------------------------------------------------------------------------

CANONICAL_VARIANTS = {
    "A": "fixed_overlap_flattened_tables_dense",
    "B": "section_aware_dense",
    "C": "self_describing_cells_and_parents",
    "D": "dense_bm25_rrf60",
    "E": "hierarchical_candidates_and_cross_encoder",
    "F": "bounded_query_routing",
    "G": "independently_approved_charts",
}


class RetrievalStageError(RuntimeError):
    """A required stage failed: callers must not generate an ordinary answer."""

    def __init__(self, code, stage, trace):
        super().__init__(f"Retrieval stage {stage} failed: {code}")
        self.code, self.stage, self.trace = code, stage, deepcopy(trace)


@dataclass(frozen=True)
class RoutingPolicy:
    """Explicit bounded development configuration, not proof of tuned thresholds.

    F tries the question's preferred stream first and at most one other stream.
    Thresholds and this exact configuration belong in the frozen run manifest.
    """

    min_candidates: int = 3
    max_tiers: int = 2
    min_cross_encoder_score: float = 0.0

    def __post_init__(self):
        if type(self.min_candidates) is not int or self.min_candidates < 1:
            raise ValueError("Routing min_candidates must be a positive integer")
        if type(self.max_tiers) is not int or self.max_tiers not in {1, 2}:
            raise ValueError("Routing max_tiers must be one or two")
        if not isinstance(self.min_cross_encoder_score, Real) or isinstance(self.min_cross_encoder_score, bool) or not math.isfinite(self.min_cross_encoder_score):
            raise ValueError("Routing score threshold must be finite")


def _configured_filters(adapter):
    configured = getattr(adapter, "filters", None)
    return configured if isinstance(configured, dict) else {}


def _identity(item):
    return item.get("evidence_id") or item.get("id")


class HybridRRFRetriever:
    """Canonical C/D/E/F components; request eligibility is common to all.

    C uses dense candidates and parent expansion. D adds lexical RRF60 fusion.
    E adds an explicit bounded section hierarchy then the injected cross-encoder.
    F adds bounded two-stream query routing and retains each attempt in its trace.
    A/B require representation-specific indexes and G an independently approved
    chart adapter; requesting them here is a typed unavailable-stage error.

    A predictor is not claimed to be bge-reranker-base merely because it exposes
    predict(). Supply the actual model identity and pin it in the run manifest.
    """

    CHART_TIER_AVAILABLE = False

    def __init__(
        self,
        dense: DenseRetriever,
        bm25: BM25Retriever,
        *,
        reranker=None,
        rrf_k: int = 60,
        expand_cell_parents: bool = True,
        parent_budget_chars: int = 12_000,
        variant: str | None = None,
        hierarchy_filters: dict | None = None,
        max_hierarchy_sections: int = 2,
        routing_policy: RoutingPolicy | None = None,
        reranker_model_id: str | None = None,
    ):
        if type(rrf_k) is not int or rrf_k != 60:
            raise ValueError("Canonical RRF k must be the positive integer 60")
        if type(parent_budget_chars) is not int or parent_budget_chars < 0:
            raise ValueError("Parent budget must be a nonnegative integer")
        if type(max_hierarchy_sections) is not int or max_hierarchy_sections < 1:
            raise ValueError("Hierarchy section limit must be positive")
        variant = variant or ("E" if reranker is not None else "D")
        if variant not in CANONICAL_VARIANTS:
            raise ValueError("Variant must be A through G")
        if variant in {"C", "D"} and reranker is not None:
            raise ValueError("Cross-encoder belongs to canonical stage E and later")
        if reranker_model_id is not None and (not isinstance(reranker_model_id, str) or not reranker_model_id.strip()):
            raise ValueError("Reranker model identity must be a nonempty string")
        self.dense, self.bm25, self.reranker = dense, bm25, reranker
        self.rrf_k = rrf_k
        self.expand_cell_parents, self.parent_budget_chars = expand_cell_parents, parent_budget_chars
        self.variant, self.hierarchy_filters = variant, validated_filters(hierarchy_filters)
        self.max_hierarchy_sections = max_hierarchy_sections
        self.routing_policy = routing_policy or RoutingPolicy()
        self.reranker_model_id = reranker_model_id

    @staticmethod
    def _fail(result, code, stage, exc=None):
        result.update(status="service_error", failure_code=code, failed_stage=stage,
                      text_evidence=[], table_evidence=[], chart_evidence=[], all_evidence=[])
        if exc is not None:
            result["error_class"] = type(exc).__name__
        raise RetrievalStageError(code, stage, result) from exc

    def _component(self, adapter, name, query, text_k, table_k, scope, result):
        if not (text_k or table_k) or empty_scope(scope):
            return [], []
        try:
            response = adapter.retrieve(query, top_k_text=text_k, top_k_tables=table_k, filters=scope)
            if not isinstance(response, dict):
                self._fail(result, "invalid_component_response", name)
            if (response.get("success") is False
                    or response.get("status") not in {None, "ok", "insufficient_evidence"}
                    or any(response.get(key) for key in (
                        "failure_code", "error_code", "text_error", "table_error", "rerank_error", "error"))):
                self._fail(result, "component_stage_failed", name)
            text = response.get("text_evidence", [])
            tables = response.get("table_evidence", [])
            if not isinstance(text, list) or not isinstance(tables, list) or len(text) > text_k or len(tables) > table_k:
                self._fail(result, "invalid_component_response", name)
            if response.get("status") == "insufficient_evidence" and (text or tables):
                self._fail(result, "contradictory_component_status", name)
            for records, kind in ((text, "narrative_text"), (tables, "table_cell")):
                ids = set()
                for record in records:
                    if not isinstance(record, dict):
                        self._fail(result, "invalid_component_evidence", name)
                    eid, metadata, content = _identity(record), record.get("metadata"), record.get("content")
                    if (not isinstance(eid, str) or not eid.strip() or eid in ids
                            or ("id" in record and record["id"] != eid)
                            or not isinstance(metadata, dict) or metadata.get("type") != kind
                            or not isinstance(content, str) or not content.strip()):
                        self._fail(result, "invalid_component_evidence", name)
                    ids.add(eid)
            if any(not eligible(record, scope) for record in text + tables):
                self._fail(result, "eligibility_violation", name)
            return text, tables
        except RetrievalStageError:
            raise
        except Exception as exc:
            self._fail(result, f"{name}_failure", name, exc)

    def _hierarchy(self, candidates, result):
        """Restrict candidate section groups, separately from request predicates."""
        allowed = [c for c in candidates if eligible(c, self.hierarchy_filters)]
        groups = []
        for candidate in allowed:
            m = candidate.get("metadata", {})
            group = (m.get("ticker"), m.get("accession"), m.get("section"))
            if group not in groups:
                groups.append(group)
        retained = set(groups[:self.max_hierarchy_sections])
        selected = [c for c in allowed if (
            c.get("metadata", {}).get("ticker"), c.get("metadata", {}).get("accession"),
            c.get("metadata", {}).get("section")) in retained]
        result["stages"].append({
            "stage": "hierarchical_candidate_restriction", "variant": "E",
            "policy": "top_ranked_section_groups", "max_sections": self.max_hierarchy_sections,
            "hierarchy_filters": deepcopy(self.hierarchy_filters),
            "retained_groups": [list(group) for group in groups[:self.max_hierarchy_sections]],
            "excluded_ids": [_identity(c) for c in candidates if c not in selected],
        })
        return selected

    def _rerank(self, query, candidates, top_n, result):
        if not candidates:
            return []
        if self.reranker is None:
            self._fail(result, "reranker_not_ready", "cross_encoder")
        try:
            raw = self.reranker.predict([[query, c.get("content", "")] for c in candidates])
            scores = raw.tolist() if hasattr(raw, "tolist") else list(raw)
            if not isinstance(scores, list) or len(scores) != len(candidates):
                raise ValueError("Cross-encoder must return exactly one score per candidate")
            if any(not isinstance(score, Real) or isinstance(score, bool) or not math.isfinite(score) for score in scores):
                raise ValueError("Cross-encoder scores must be finite scalar numbers")
            scored = [{**deepcopy(c), "cross_encoder_score": float(score)}
                      for c, score in zip(candidates, scores, strict=True)]
            ordered = sorted(scored, key=lambda c: (-c["cross_encoder_score"], _identity(c)))[:top_n]
            result["stages"].append({
                "stage": "cross_encoder_rerank", "variant": "E",
                "model": self.reranker_model_id or "unverified injected predictor",
                "model_identity_verified": False, "top_n": top_n,
                "input_count": len(candidates), "output_count": len(ordered),
            })
            return ordered
        except Exception as exc:
            self._fail(result, "reranker_failed", "cross_encoder", exc)

    def _attempt(self, query, text_k, table_k, scope, parents, top_n, result):
        dense_text, dense_tables = self._component(
            self.dense, "dense", query, text_k, table_k, scope, result)
        result["stages"].append({"stage": "dense", "text_count": len(dense_text),
                                 "table_count": len(dense_tables)})
        if self.variant == "C":
            text, tables = dense_text, dense_tables
        else:
            bm_text, bm_tables = self._component(
                self.bm25, "bm25", query, text_k, table_k, scope, result)
            result["stages"].append({"stage": "bm25", "variant": "D",
                                     "text_count": len(bm_text), "table_count": len(bm_tables)})
            try:
                text = reciprocal_rank_fusion([dense_text, bm_text], k=self.rrf_k)
                tables = reciprocal_rank_fusion([dense_tables, bm_tables], k=self.rrf_k)
            except ValueError as exc:
                self._fail(result, "evidence_identity_conflict", "rrf_fusion", exc)
            result["stages"].append({"stage": "rrf_fusion", "variant": "D", "rrf_k": 60,
                                     "text_count": len(text), "table_count": len(tables)})
        candidates = sorted(text + tables, key=lambda c: (
            -c.get("rrf_score", c.get("score", 0.0)), _identity(c)))
        if self.variant in {"E", "F"}:
            candidates = self._hierarchy(candidates, result)
        if self.expand_cell_parents:
            before = len(candidates)
            try:
                candidates = expand_parents(
                    candidates, parents, budget_chars=self.parent_budget_chars,
                    already_included=set())
            except ValueError as exc:
                self._fail(result, "invalid_parent_evidence", "parent_expansion", exc)
            result["stages"].append({"stage": "parent_expansion", "variant": "C",
                                     "injected_parents": sum(c.get("expansion") == "parent_of_cell" for c in candidates),
                                     "input_count": before, "output_count": len(candidates)})
        result["candidate_evidence_ids"] = [_identity(c) for c in candidates]
        if self.variant in {"E", "F"}:
            candidates = self._rerank(query, candidates, top_n, result)
        return candidates

    def retrieve(
        self, query: str, top_k_text: int = 5, top_k_tables: int = 5, *,
        rerank_top_n: int = 5, routing: dict[str, bool] | None = None,
        store_parents: dict[str, dict[str, Any]] | None = None,
        filters: dict | None = None,
    ) -> dict[str, Any]:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query must be a nonempty string")
        if any(type(k) is not int or k < 0 for k in (top_k_text, top_k_tables)):
            raise ValueError("Retrieval budgets must be nonnegative integers")
        if type(rerank_top_n) is not int or rerank_top_n < 1:
            raise ValueError("rerank_top_n must be a positive integer")
        routing = {} if routing is None else routing
        if not isinstance(routing, dict) or set(routing) - {"narrative", "table", "chart"} or any(type(v) is not bool for v in routing.values()):
            raise ValueError("Routing accepts only narrative/table/chart boolean switches")
        scope = intersect_filters(_configured_filters(self.dense), _configured_filters(self.bm25), filters)
        text_k = top_k_text if routing.get("narrative", True) else 0
        table_k = top_k_tables if routing.get("table", True) else 0
        result = {
            "query": query, "retrieval_mode": "dense_only" if self.variant == "C" else "hybrid_rrf",
            "variant": self.variant, "variant_definition": CANONICAL_VARIANTS[self.variant],
            "status": "ok", "eligibility_filters": scope, "stages": [], "ranking_applied": True,
            "text_evidence": [], "table_evidence": [], "chart_evidence": [],
            "all_evidence": [], "ranked_evidence_ids": [], "candidate_evidence_ids": [],
            "routing": {"narrative": bool(text_k), "table": bool(table_k), "chart": False,
                        "chart_blocked_reason": "No independently approved chart adapter",
                        "attempts": []},
            "experimental_readiness": "component_only; frozen inputs and complete A-G run evidence required",
        }
        if self.variant in {"A", "B"}:
            self._fail(result, "variant_not_ready", "representation_index")
        if self.variant == "G":
            self._fail(result, "chart_not_ready", "chart_evidence")
        if self.variant in {"E", "F"} and self.reranker is None:
            self._fail(result, "reranker_not_ready", "cross_encoder")
        if not (text_k or table_k) or empty_scope(scope):
            result.update(status="insufficient_evidence", insufficient_evidence=True)
            return result
        if store_parents is None:
            store = getattr(self.dense, "store", None)
            candidate_parents = getattr(store, "parents", None)
            store_parents = candidate_parents if isinstance(candidate_parents, dict) else {}
        if not isinstance(store_parents, dict):
            raise ValueError("Parent tables must be a dictionary")
        attempts = [(text_k, table_k)]
        if self.variant == "F":
            if re.search(r"\b(chart|graph|plot)\b", query.lower()):
                result["routing"].update(question_kind="chart", stop_reason="chart_tier_unavailable_before_G")
                result.update(status="insufficient_evidence", insufficient_evidence=True)
                return result
            numerical = bool(re.search(r"\b(revenue|sales|cost|profit|margin|growth|percent|ratio|total|how much|how many)\b", query.lower()))
            preferred = (0, table_k) if numerical else (text_k, 0)
            other = (text_k, 0) if numerical else (0, table_k)
            attempts = [ks for ks in (preferred, other) if any(ks)]
            attempts = attempts[:self.routing_policy.max_tiers]
            result["routing"].update(
                question_kind="numerical" if numerical else "narrative",
                policy={"min_candidates": self.routing_policy.min_candidates,
                        "max_tiers": self.routing_policy.max_tiers,
                        "min_cross_encoder_score": self.routing_policy.min_cross_encoder_score},
                thresholds_provenance="configuration; not evidence of development tuning",
            )
        cumulative_text, cumulative_table, candidates = 0, 0, []
        for attempt, (current_text, current_table) in enumerate(attempts, 1):
            cumulative_text = max(cumulative_text, current_text)
            cumulative_table = max(cumulative_table, current_table)
            candidates = self._attempt(query, cumulative_text, cumulative_table, scope,
                                       store_parents, rerank_top_n, result)
            enough = len(candidates) >= self.routing_policy.min_candidates
            confident = bool(candidates) and (
                self.variant != "F" or candidates[0].get("cross_encoder_score", float("-inf")) >= self.routing_policy.min_cross_encoder_score)
            result["routing"]["attempts"].append({
                "tier": attempt, "narrative_limit": cumulative_text, "table_limit": cumulative_table,
                "ranked_ids": [_identity(c) for c in candidates],
                "stop_reason": "thresholds_satisfied" if enough and confident else "bounded_escalation_or_shortfall",
            })
            if self.variant != "F" or (enough and confident):
                break
        if self.variant == "F" and candidates and (not confident or not enough):
            # Exhausting the bound below the declared score threshold is an
            # abstention, never a successful-looking fallback final variant.
            result["routing"]["stop_reason"] = (
                "score_threshold_not_met" if not confident else "candidate_threshold_not_met")
            result["rejected_evidence_ids"] = [_identity(c) for c in candidates]
            candidates = []
        result["text_evidence"] = [c for c in candidates if c.get("metadata", {}).get("type") == "narrative_text"]
        result["table_evidence"] = [c for c in candidates if c.get("metadata", {}).get("type") in {"table_cell", "financial_table"}]
        result["all_evidence"] = candidates
        result["ranked_evidence_ids"] = [_identity(c) for c in candidates]
        # Only the engine that actually renders the prompt can assign included IDs.
        result["insufficient_evidence"] = not bool(candidates)
        result["status"] = "ok" if candidates else "insufficient_evidence"
        return result
