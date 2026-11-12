"""
Hierarchical Reranking Module (Member 2: Sprint 4)
Reranks combined text chunks and financial tables to maximize quantitative relevance.
"""

import math
import re
from numbers import Real
from typing import Any


class SimpleFinancialReranker:
    """
    Reranks retrieved candidate items (text chunks and tables) based on semantic overlap
    and financial specificity (years, currency, percentages, keywords).
    Supports pluggable neural cross-encoder models.
    """

    def __init__(self, cross_encoder_model=None):
        self.cross_encoder_model = cross_encoder_model

    def _heuristic_score(self, query: str, content: str, doc_type: str) -> float:
        score = 0.0
        query_terms = set(re.findall(r"\w+", query.lower()))
        content_lower = content.lower()

        # Term overlap
        for term in query_terms:
            if term in content_lower:
                score += 2.0

        # Quantitative density indicators
        dollar_count = len(re.findall(r"\$[\d,]+", content))
        percent_count = len(re.findall(r"\d+(\.\d+)?%", content))
        year_matches = len(re.findall(r"\b(19\d\d|20\d\d)\b", content))

        score += min(dollar_count * 0.5, 3.0)
        score += min(percent_count * 0.5, 2.0)
        score += min(year_matches * 0.5, 2.0)

        # Priority boost for tables
        if doc_type in ["financial_table", "clean_financial_table"]:
            score += 2.5

        return score

    def rerank(
        self,
        query: str,
        candidates: list[dict[str, Any]],
        top_n: int = 4,
    ) -> list[dict[str, Any]]:
        """
        Reranks candidates and returns top_n items.
        """
        if type(top_n) is not int or top_n < 1:
            raise ValueError("Reranking limit must be a positive integer.")
        if not candidates:
            return []

        # Never mutate the stored/shared evidence or accept a partial model result.
        candidates = [dict(candidate) for candidate in candidates]
        if self.cross_encoder_model is not None:
            pairs = [[query, c["content"]] for c in candidates]
            scores = list(self.cross_encoder_model.predict(pairs))
            if len(scores) != len(candidates):
                raise ValueError("Cross-encoder returned an inconsistent score count.")
            if any(isinstance(score, bool) or not isinstance(score, Real) for score in scores):
                raise ValueError("Cross-encoder scores must be real numerical scalars.")
            scores = [float(score) for score in scores]
            if not all(math.isfinite(score) for score in scores):
                raise ValueError("Cross-encoder returned an invalid score.")
            for i, c in enumerate(candidates):
                c["rerank_score"] = scores[i]
        else:
            for c in candidates:
                doc_type = c.get("metadata", {}).get("type", "narrative_text")
                c["rerank_score"] = self._heuristic_score(query, c["content"], doc_type)

        ranked = sorted(candidates, key=lambda x: x.get("rerank_score", 0.0), reverse=True)
        return ranked[:top_n]
