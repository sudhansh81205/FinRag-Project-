"""Evaluation metrics for FinRAG benchmarks (PRD R7/R12).

Implements 1% relative numerical tolerance, zero-gold tolerance,
Recall@5, Recall@10, MRR, RAGAS-style faithfulness estimation,
and paired 95% bootstrap confidence intervals.
"""

import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any

from .loaders import GoldReference


@dataclass
class EvaluatorMetrics:
    total_cases: int = 0
    successful_cases: int = 0
    failed_cases: int = 0
    refused_cases: int = 0
    numerical_correct: int = 0
    numerical_total: int = 0
    exact_match_correct: int = 0
    exact_match_total: int = 0
    recall_at_5_sum: float = 0.0
    recall_at_10_sum: float = 0.0
    mrr_sum: float = 0.0
    retrieval_cases: int = 0
    complete_evidence_count: int = 0
    faithfulness_scores: list[float] = field(default_factory=list)
    latencies: list[float] = field(default_factory=list)
    failure_reasons: dict[str, int] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        """Compute aggregated summary dictionary."""
        num_acc = (self.numerical_correct / self.numerical_total) if self.numerical_total > 0 else 0.0
        em_acc = (self.exact_match_correct / self.exact_match_total) if self.exact_match_total > 0 else 0.0
        r5 = (self.recall_at_5_sum / self.retrieval_cases) if self.retrieval_cases > 0 else 0.0
        r10 = (self.recall_at_10_sum / self.retrieval_cases) if self.retrieval_cases > 0 else 0.0
        mrr = (self.mrr_sum / self.retrieval_cases) if self.retrieval_cases > 0 else 0.0
        complete_ev_rate = (self.complete_evidence_count / self.retrieval_cases) if self.retrieval_cases > 0 else 0.0
        avg_faith = (sum(self.faithfulness_scores) / len(self.faithfulness_scores)) if self.faithfulness_scores else 0.0
        
        sorted_lat = sorted(self.latencies) if self.latencies else [0.0]
        median_lat = sorted_lat[len(sorted_lat) // 2]
        mean_lat = sum(sorted_lat) / len(sorted_lat) if sorted_lat else 0.0

        return {
            "total_cases": self.total_cases,
            "successful_cases": self.successful_cases,
            "failed_cases": self.failed_cases,
            "refused_cases": self.refused_cases,
            "numerical_accuracy": round(num_acc, 4),
            "numerical_cases": self.numerical_total,
            "exact_match_accuracy": round(em_acc, 4),
            "exact_match_cases": self.exact_match_total,
            "recall_at_5": round(r5, 4),
            "recall_at_10": round(r10, 4),
            "mrr": round(mrr, 4),
            "complete_evidence_rate": round(complete_ev_rate, 4),
            "retrieval_cases": self.retrieval_cases,
            "faithfulness_mean": round(avg_faith, 4),
            "median_latency_seconds": round(median_lat, 3),
            "mean_latency_seconds": round(mean_lat, 3),
            "failure_reasons": dict(self.failure_reasons),
        }


def extract_first_decimal(text: str) -> Decimal | None:
    """Extract first numeric amount or percentage from string."""
    if not isinstance(text, str):
        return None
    cleaned = text.replace(",", "").replace("$", "").replace("%", "").strip()
    match = re.search(r"[-+]?\d*\.?\d+", cleaned)
    if not match:
        return None
    try:
        return Decimal(match.group(0))
    except InvalidOperation:
        return None


def evaluate_numerical_match(
    predicted_val: Decimal | float | int | str | None,
    gold: GoldReference,
) -> bool:
    """Evaluate numerical answer within 1% relative tolerance or zero tolerance."""
    if predicted_val is None:
        return False
    
    if isinstance(predicted_val, str):
        pred_dec = extract_first_decimal(predicted_val)
        if pred_dec is None:
            return False
    else:
        try:
            pred_dec = Decimal(str(predicted_val))
        except InvalidOperation:
            return False

    gold_val = gold.gold_value_numeric
    if gold_val is None and isinstance(gold.gold_answer, str):
        gold_dec = extract_first_decimal(gold.gold_answer)
    elif gold_val is not None:
        try:
            gold_dec = Decimal(str(gold_val))
        except InvalidOperation:
            gold_dec = None
    else:
        gold_dec = None

    if gold_dec is None:
        return False

    # Zero tolerance check
    if abs(gold_dec) <= Decimal(str(gold.zero_tolerance)):
        return abs(pred_dec) <= Decimal(str(gold.zero_tolerance))

    # 1% relative tolerance check: |pred - gold| / |gold| <= 0.01
    rel_error = abs(pred_dec - gold_dec) / abs(gold_dec)
    return rel_error <= Decimal(str(gold.relative_tolerance))


def normalize_text(text: str) -> str:
    """Normalize text for exact match scoring."""
    lower = text.lower()
    no_punct = re.sub(r"[^\w\s]", " ", lower)
    return " ".join(no_punct.split())


def evaluate_text_match(predicted: str, gold: GoldReference) -> bool:
    """Check exact match between normalized strings."""
    if not isinstance(predicted, str) or not predicted.strip():
        return False
    pred_norm = normalize_text(predicted)
    
    if isinstance(gold.gold_answer, list):
        return any(normalize_text(ans) in pred_norm for ans in gold.gold_answer)
    return normalize_text(str(gold.gold_answer)) in pred_norm


def evaluate_retrieval(
    ranked_evidence_ids: list[str],
    gold_evidence_ids: tuple[str, ...],
) -> tuple[float, float, float, bool]:
    """Calculate Recall@5, Recall@10, MRR, and complete evidence presence.

    Returns (recall@5, recall@10, mrr, complete_evidence_bool).
    """
    if not gold_evidence_ids:
        return 0.0, 0.0, 0.0, True

    gold_set = set(gold_evidence_ids)
    top_5 = ranked_evidence_ids[:5]
    top_10 = ranked_evidence_ids[:10]

    hits_5 = len(set(top_5) & gold_set)
    hits_10 = len(set(top_10) & gold_set)

    r5 = hits_5 / len(gold_set)
    r10 = hits_10 / len(gold_set)

    mrr = 0.0
    for rank, eid in enumerate(ranked_evidence_ids, start=1):
        if eid in gold_set:
            mrr = 1.0 / rank
            break

    complete = gold_set.issubset(set(top_5))
    return r5, r10, mrr, complete


def estimate_faithfulness(answer_text: str, evidence_blocks: list[str]) -> float:
    """RAGAS-style faithfulness heuristic: fraction of answer sentences grounded in context."""
    if not answer_text.strip() or not evidence_blocks:
        return 0.0
    full_context = " ".join(evidence_blocks).lower()
    sentences = [s.strip() for s in re.split(r"[.!?]", answer_text) if len(s.strip()) > 10]
    if not sentences:
        return 1.0 if answer_text.strip() else 0.0
    
    grounded = 0
    for sent in sentences:
        words = [w for w in normalize_text(sent).split() if len(w) > 3]
        if not words:
            grounded += 1
            continue
        matches = sum(1 for w in words if w in full_context)
        if matches / len(words) >= 0.5:
            grounded += 1
    return grounded / len(sentences)


def compute_all_metrics(
    eval_results: list[dict[str, Any]],
    gold_refs: dict[str, GoldReference],
) -> EvaluatorMetrics:
    """Compute complete metric suite across all evaluation results."""
    m = EvaluatorMetrics(total_cases=len(eval_results))

    for res in eval_results:
        cid = res["case_id"]
        gold = gold_refs.get(cid)
        if gold is None:
            continue

        status = res.get("status", "unknown")
        latency = float(res.get("latency_seconds", 0.0))
        m.latencies.append(latency)

        if status == "ok":
            m.successful_cases += 1
        elif status in {"insufficient_evidence", "invalid_request"}:
            m.refused_cases += 1
            reason = res.get("message", status)
            m.failure_reasons[reason] = m.failure_reasons.get(reason, 0) + 1
        else:
            m.failed_cases += 1
            reason = res.get("message", status)
            m.failure_reasons[reason] = m.failure_reasons.get(reason, 0) + 1

        # Retrieval scoring
        ranked_ids = res.get("ranked_evidence_ids", res.get("included_evidence_ids", []))
        if gold.gold_evidence_ids:
            r5, r10, mrr, complete = evaluate_retrieval(ranked_ids, gold.gold_evidence_ids)
            m.recall_at_5_sum += r5
            m.recall_at_10_sum += r10
            m.mrr_sum += mrr
            if complete:
                m.complete_evidence_count += 1
            m.retrieval_cases += 1

        # Answer scoring
        pred_ans = res.get("answer", "")
        if gold.gold_value_numeric is not None or (isinstance(gold.gold_answer, str) and extract_first_decimal(gold.gold_answer) is not None):
            m.numerical_total += 1
            if status == "ok" and evaluate_numerical_match(pred_ans, gold):
                m.numerical_correct += 1
        else:
            m.exact_match_total += 1
            if status == "ok" and evaluate_text_match(pred_ans, gold):
                m.exact_match_correct += 1

        # Faithfulness
        evidence_texts = [e.get("content", "") for e in res.get("evidence", []) if isinstance(e, dict)]
        if status == "ok" and pred_ans:
            m.faithfulness_scores.append(estimate_faithfulness(pred_ans, evidence_texts))

    return m


def compute_paired_intervals(
    scores_a: list[float],
    scores_b: list[float],
    n_bootstrap: int = 1000,
    seed: int = 42,
) -> tuple[float, float]:
    """Compute 95% bootstrap confidence interval for the difference (scores_a - scores_b)."""
    import random
    if not scores_a or len(scores_a) != len(scores_b):
        return 0.0, 0.0

    rng = random.Random(seed)
    n = len(scores_a)
    diffs = [a - b for a, b in zip(scores_a, scores_b)]
    means = []

    for _ in range(n_bootstrap):
        sample = [diffs[rng.randint(0, n - 1)] for _ in range(n)]
        means.append(sum(sample) / n)

    means.sort()
    lower_idx = int(0.025 * n_bootstrap)
    upper_idx = int(0.975 * n_bootstrap)
    return round(means[lower_idx], 4), round(means[upper_idx], 4)
