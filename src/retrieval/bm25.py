"""BM25 retriever and Reciprocal Rank Fusion (RRF) hybrid for FinRAG.

Pavan's November 7 task: implement A-F cumulative retrieval stages.

BM25 provides lexical/exact-term matching over the same canonical candidate
set used by the dense index. RRF combines dense and BM25 rankings without
needing score calibration.  The chart tier (stage G) remains disabled until
accepted chart descriptions exist.

Stage mapping:
  A - dense-only narrative/table, no filters                 (DenseRetriever)
  B - dense, section-aware chunk filters                     (DenseRetriever + filters)
  C - dense + cell parent expansion                          (this module)
  D - BM25 alone                                             (BM25Retriever)
  E - dense + BM25 fused with RRF k=60                       (HybridRRFRetriever)
  F - E + bge-reranker-base cross-encoder, routing           (HybridRRFRetriever + rerank)
  G - F + chart evidence tier (blocked; no accepted captions yet)
"""

import math
import re
from collections import defaultdict
from typing import Any

from .dense import DenseRetriever

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
        self.records = records
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
        if k == 0:
            return []
        filters = filters or {}
        eligible = [
            i for i, record in enumerate(self.records)
            if _eligible(record, filters)
        ]
        if not eligible:
            return []
        scored = sorted(
            ((self.score(query, i), i) for i in eligible),
            key=lambda pair: (-pair[0], self.records[pair[1]]["evidence_id"]),
        )[:k]
        return [
            {
                **self.records[row],
                "bm25_score": score,
                "bm25_rank": rank,
                "eligible_count": len(eligible),
            }
            for rank, (score, row) in enumerate(scored, 1)
        ]


def _eligible(record: dict[str, Any], filters: dict) -> bool:
    """Return True when the record matches all filter key/value constraints."""
    for key, value in filters.items():
        actual = record.get("metadata", {}).get(key)
        if isinstance(value, list):
            if actual not in value:
                return False
        else:
            if actual != value:
                return False
    return True


# ---------------------------------------------------------------------------
# BM25Retriever: stage D — same interface as DenseRetriever
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
        self.filters = dict(filters or {})
        if "type" in self.filters:
            raise ValueError("Use stream limits for the record type filter")
        # Build one index per stream type, populated lazily.
        self._narrative_records = [r for r in records if r["metadata"].get("type") == "narrative_text"]
        self._cell_records = [r for r in records if r["metadata"].get("type") == "table_cell"]
        self._narrative_index: BM25Index | None = (
            BM25Index(self._narrative_records) if self._narrative_records else None
        )
        self._cell_index: BM25Index | None = (
            BM25Index(self._cell_records) if self._cell_records else None
        )

    def retrieve(self, query: str, top_k_text: int = 3, top_k_tables: int = 3) -> dict[str, Any]:
        if any(type(k) is not int or k < 0 for k in (top_k_text, top_k_tables)):
            raise ValueError("Retrieval budgets must be nonnegative integers")
        result: dict[str, Any] = {
            "query": query,
            "text_evidence": [],
            "table_evidence": [],
            "retrieval_mode": "bm25_only",
        }
        if not (top_k_text or top_k_tables):
            return result
        if top_k_text and self._narrative_index is not None:
            result["text_evidence"] = self._narrative_index.search(
                query, k=top_k_text, filters=self.filters
            )
        if top_k_tables and self._cell_index is not None:
            result["table_evidence"] = self._cell_index.search(
                query, k=top_k_tables, filters=self.filters
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
    if k <= 0:
        raise ValueError("RRF constant k must be positive")
    rrf_scores: dict[str, float] = defaultdict(float)
    component_ranks: dict[str, dict[str, int]] = defaultdict(dict)
    # Map evidence_id -> canonical record (first occurrence wins)
    id_to_item: dict[str, dict[str, Any]] = {}
    for list_index, ranked in enumerate(ranked_lists):
        for rank, item in enumerate(ranked, 1):
            eid = item.get(id_key) or item.get("id")
            if not isinstance(eid, str) or not eid.strip():
                continue
            rrf_scores[eid] += 1.0 / (k + rank)
            component_ranks[eid][f"list_{list_index}_rank"] = rank
            if eid not in id_to_item:
                id_to_item[eid] = item
    fused = sorted(
        rrf_scores.items(),
        key=lambda pair: (-pair[1], pair[0]),
    )
    return [
        {
            **id_to_item[eid],
            "rrf_score": score,
            "rrf_component_ranks": component_ranks[eid],
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
    """Inject a cell's parent table once, within the shared character budget.

    For each ``table_cell`` candidate whose parent has not yet been included,
    prepend the parent record if it fits in the remaining budget.  The budget
    is updated in place (tracked via a mutable one-element list to allow the
    helper to mutate it without returning it).

    Returns a new list that may contain parent records inserted before their
    child cells.  Candidates that have no parent in ``store_parents`` are
    passed through unchanged.

    This implements stage C parent expansion.  The caller is responsible for
    deduplication and final token-budget enforcement.
    """
    expanded: list[dict[str, Any]] = []
    used_chars = [0]  # mutable surrogate for nonlocal

    def fits(item: dict[str, Any]) -> bool:
        cost = len(item.get("content", "")) + 20  # slack for ID prefix
        if used_chars[0] + cost > budget_chars:
            return False
        used_chars[0] += cost
        return True

    for candidate in candidates:
        eid = candidate.get("evidence_id", candidate.get("id", ""))
        kind = candidate.get("metadata", {}).get("type")
        if kind == "table_cell":
            parent_id = candidate.get("metadata", {}).get("parent_table_id")
            if parent_id and parent_id not in already_included:
                parent = store_parents.get(parent_id)
                if parent is not None and fits(parent):
                    already_included.add(parent_id)
                    expanded.append({**parent, "expansion": "parent_of_cell"})
        if fits(candidate):
            expanded.append(candidate)
    return expanded


# ---------------------------------------------------------------------------
# HybridRRFRetriever: stages E and F
# ---------------------------------------------------------------------------

class HybridRRFRetriever:
    """Dense + BM25 fused with RRF (stage E) with optional cross-encoder reranking (stage F).

    When ``reranker`` is None the output is stage-E (fused, no cross-encoder).
    When ``reranker`` is provided it must expose a ``predict(pairs)`` method
    (compatible with sentence-transformers CrossEncoder).

    ``expand_cell_parents`` enables stage-C parent expansion before reranking.
    Set it to False for stage-E standalone to skip parent injection.

    The ``routing`` dict lets callers disable streams entirely:
      ``{"narrative": False}`` → table-only retrieval (stream disabled, no query)
      ``{"chart": False}``     → chart tier blocked (always False until G is ready)

    Disabled streams issue no retrieval call, consistent with the PR7 contract.
    """

    # Chart tier is always blocked until accepted descriptions exist.
    CHART_TIER_AVAILABLE = False

    def __init__(
        self,
        dense: "DenseRetriever",
        bm25: BM25Retriever,
        *,
        reranker=None,
        rrf_k: int = 60,
        expand_cell_parents: bool = True,
        parent_budget_chars: int = 12_000,
    ):
        if rrf_k <= 0:
            raise ValueError("RRF k must be a positive integer")
        self.dense = dense
        self.bm25 = bm25
        self.reranker = reranker
        self.rrf_k = rrf_k
        self.expand_cell_parents = expand_cell_parents
        self.parent_budget_chars = parent_budget_chars

    def retrieve(
        self,
        query: str,
        top_k_text: int = 5,
        top_k_tables: int = 5,
        *,
        rerank_top_n: int = 5,
        routing: dict[str, bool] | None = None,
        store_parents: dict[str, dict[str, Any]] | None = None,
        filters: dict | None = None,
    ) -> dict[str, Any]:
        """Return fused + optionally reranked evidence.

        Parameters
        ----------
        query:
            Free-text question.
        top_k_text:
            Maximum narrative candidates per retriever before fusion.
        top_k_tables:
            Maximum cell/table candidates per retriever before fusion.
        rerank_top_n:
            How many fused candidates to pass through the cross-encoder
            (stage F). Ignored when ``reranker`` is None.
        routing:
            Dict of stream name → bool.  ``False`` disables that stream.
            Supported keys: ``"narrative"``, ``"table"``.
        store_parents:
            ``ExactStore.parents`` dict for stage-C parent expansion.
            Required only when ``expand_cell_parents=True``.
        filters:
            Eligibility filters forwarded to both dense and BM25 search.
        """
        if any(type(k) is not int or k < 0 for k in (top_k_text, top_k_tables)):
            raise ValueError("Retrieval budgets must be nonnegative integers")
        if type(rerank_top_n) is not int or rerank_top_n < 1:
            raise ValueError("rerank_top_n must be a positive integer")
        routing = routing or {}
        narrative_on = routing.get("narrative", True)
        table_on = routing.get("table", True)
        chart_on = routing.get("chart", True) and self.CHART_TIER_AVAILABLE

        result: dict[str, Any] = {
            "query": query,
            "retrieval_mode": "hybrid_rrf",
            "stages": [],
            "text_evidence": [],
            "table_evidence": [],
            "chart_evidence": [],  # always empty until stage G
            "routing": {
                "narrative": narrative_on,
                "table": table_on,
                "chart": chart_on,
                "chart_blocked_reason": "No accepted chart descriptions yet" if not chart_on else None,
            },
        }

        # --- Stage A/B: Dense retrieval (filtered) ---
        actual_text_k = top_k_text if narrative_on else 0
        actual_table_k = top_k_tables if table_on else 0
        dense_result = self.dense.retrieve(
            query, top_k_text=actual_text_k, top_k_tables=actual_table_k
        )
        dense_text = dense_result.get("text_evidence", [])
        dense_table = dense_result.get("table_evidence", [])
        result["stages"].append({
            "stage": "dense",
            "text_count": len(dense_text),
            "table_count": len(dense_table),
        })

        # --- Stage D: BM25 retrieval (same filters) ---
        bm25_result = self.bm25.retrieve(
            query, top_k_text=actual_text_k, top_k_tables=actual_table_k
        )
        bm25_text = bm25_result.get("text_evidence", [])
        bm25_table = bm25_result.get("table_evidence", [])
        result["stages"].append({
            "stage": "bm25",
            "text_count": len(bm25_text),
            "table_count": len(bm25_table),
        })

        # --- Stage E: RRF fusion ---
        fused_text = reciprocal_rank_fusion(
            [dense_text, bm25_text], k=self.rrf_k
        ) if narrative_on else []
        fused_table = reciprocal_rank_fusion(
            [dense_table, bm25_table], k=self.rrf_k
        ) if table_on else []
        result["stages"].append({
            "stage": "rrf_fusion",
            "rrf_k": self.rrf_k,
            "text_count": len(fused_text),
            "table_count": len(fused_table),
        })

        # --- Stage C: Parent expansion ---
        all_candidates: list[dict[str, Any]] = []
        if self.expand_cell_parents and store_parents is not None:
            already: set[str] = set()
            expanded = expand_parents(
                fused_table,
                store_parents,
                budget_chars=self.parent_budget_chars,
                already_included=already,
            )
            all_candidates = fused_text + expanded
            result["stages"].append({
                "stage": "parent_expansion",
                "injected_parents": len(already),
                "total_candidates": len(all_candidates),
            })
        else:
            all_candidates = fused_text + fused_table

        if not all_candidates:
            result["insufficient_evidence"] = True
            return result

        # --- Stage F: Cross-encoder reranking ---
        if self.reranker is not None:
            pairs = [[query, c.get("content", "")] for c in all_candidates]
            try:
                scores = self.reranker.predict(pairs)
                for item, score in zip(all_candidates, scores):
                    item["cross_encoder_score"] = float(score)
                all_candidates = sorted(
                    all_candidates,
                    key=lambda x: (-x.get("cross_encoder_score", 0.0), x.get("evidence_id", "")),
                )[:rerank_top_n]
                result["stages"].append({
                    "stage": "cross_encoder_rerank",
                    "model": "bge-reranker-base",
                    "top_n": rerank_top_n,
                    "output_count": len(all_candidates),
                })
            except Exception as exc:
                result["rerank_error"] = str(exc)
                all_candidates = all_candidates[:rerank_top_n]

        # Separate back into streams for the caller
        result["text_evidence"] = [
            c for c in all_candidates
            if c.get("metadata", {}).get("type") == "narrative_text"
        ]
        result["table_evidence"] = [
            c for c in all_candidates
            if c.get("metadata", {}).get("type") in {"table_cell", "financial_table"}
        ]
        result["all_evidence"] = all_candidates
        result["included_evidence_ids"] = [
            c.get("evidence_id", c.get("id", "")) for c in all_candidates
        ]
        return result
