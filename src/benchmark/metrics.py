"""Evaluation metrics for FinRAG benchmarks (PRD R7/R12; common A-G scoring).

* Numerical answers are scored on a structured quantity (value, scale, percent/currency)
  after normalization to base units, then compared with the 1 percent relative rule or the
  declared zero-gold absolute tolerance (F29). Equivalent scales match (100 million ==
  0.1 billion) and wrong scales fail (100 million != 100 billion).
* Text answers report three separately named measures: strict normalized exact match,
  all-gold-spans-contained (a named rubric, so a multi-span gold needs *every* span) and
  token F1 (F29).
* ``lexical_overlap_diagnostic`` is NOT RAGAS. It is a cheap heuristic kept only as a
  labelled diagnostic; the RAGAS field stays BLOCKED until a pinned evaluator has actually
  run with exact included contexts (F30).
* Paired bootstrap intervals default to the PRD's 10,000 resamples.

KR&R concept: typed quantities (value/scale/unit) must be comparable before an inference
or a score is licensed. Viva: why must scale be normalized before applying a relative
error threshold?
"""

import random
import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any

from .loaders import GoldReference

# ---------------------------------------------------------------------------
# Structured quantity parsing (F29)
# ---------------------------------------------------------------------------
_SCALE_POWER10: dict[str, int] = {
    "trillion": 12, "tn": 12, "billion": 9, "bn": 9, "b": 9,
    "million": 6, "mn": 6, "m": 6, "thousand": 3, "k": 3,
}

_NUMBER_RE = re.compile(
    r"(?<![\w.])(?P<open>\()?\s*(?P<cur>\$)?\s*(?P<sign>[-+])?"
    r"(?P<num>\d[\d,]*(?:\.\d+)?|\.\d+)\s*(?P<pct>%)?"
    r"(?:\s*(?P<scale>trillion|billion|million|thousand|tn|bn|mn|[kmb])(?![A-Za-z]))?",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ParsedQuantity:
    value: Decimal               # displayed number, signed
    scale_power10: int | None    # explicit scale word, else None (not stated)
    is_percent: bool
    has_currency: bool
    currency: str | None = None
    unit: str | None = None

    @property
    def normalized(self) -> Decimal:
        return self.value.scaleb(self.scale_power10 or 0)


def parse_quantity(text: Any) -> ParsedQuantity | None:
    """Parse the most plausible answer quantity from text.

    A number carrying a scale word, percent sign or currency symbol outranks a bare number,
    and bare 4-digit years are used only when nothing else exists, so "fiscal 2021 revenue
    was $100 million" yields 100 million rather than 2021.
    """
    if not isinstance(text, str):
        return None
    currencies = set(re.findall(r"\b(?:USD|EUR|JPY|GBP|INR|CAD|AUD|CHF|CNY)\b", text.upper()))
    for symbol, code in (("$", "USD"), ("€", "EUR"), ("£", "GBP"), ("₹", "INR"), ("¥", "JPY")):
        if symbol in text:
            currencies.add(code)
    currency = next(iter(currencies)) if len(currencies) == 1 else ("AMBIGUOUS" if currencies else None)
    unit = ("percentage_points" if re.search(r"percentage[ -]points?|\bpp\b", text, re.I)
            else "percent" if re.search(r"%|\bpercent(?:age)?\b", text, re.I)
            else "shares" if re.search(r"\bshares\b", text, re.I) else None)
    candidates: list[ParsedQuantity] = []
    for m in _NUMBER_RE.finditer(text):
        try:
            value = Decimal(m.group("num").replace(",", ""))
        except InvalidOperation:
            continue
        if m.group("sign") == "-" or (m.group("open") and text[m.end():m.end() + 1] == ")"):
            value = -value
        scale = m.group("scale")
        candidates.append(ParsedQuantity(
            value=value,
            scale_power10=_SCALE_POWER10[scale.lower()] if scale else None,
            is_percent=bool(m.group("pct")) or unit == "percent",
            has_currency=bool(m.group("cur")),
            currency=currency, unit=unit,
        ))
    if not candidates:
        return None
    for c in candidates:
        if c.scale_power10 is not None or c.is_percent or c.has_currency:
            return c
    for c in candidates:
        if not (c.value == c.value.to_integral_value() and Decimal(1900) <= abs(c.value) <= Decimal(2100)):
            return c
    return candidates[0]


def extract_first_decimal(text: str) -> Decimal | None:
    """Return the displayed (unscaled) number of the parsed quantity, if any."""
    q = parse_quantity(text)
    return q.value if q else None


@dataclass(frozen=True)
class NumericalScore:
    correct: bool
    reason: str
    predicted_normalized: Decimal | None = None
    gold_normalized: Decimal | None = None
    relative_error: Decimal | None = None
    scale_inherited: bool = False


def score_numerical(
    predicted: Decimal | float | int | str | None,
    gold: GoldReference,
) -> NumericalScore:
    """Score a numerical answer after normalizing value, scale and percent/currency units.

    Gold ``gold_value_numeric`` is the displayed number of ``gold_answer`` (so 45000.0 with
    "45,000 million USD" means 45 billion). A predicted number with no stated scale inherits
    the gold's declared display scale and is flagged; an explicit wrong scale fails.
    """
    if predicted is None:
        return NumericalScore(False, "no_prediction")
    if isinstance(predicted, str):
        pq = parse_quantity(predicted)
        if pq is None:
            return NumericalScore(False, "no_number_in_prediction")
    else:
        try:
            pq = ParsedQuantity(Decimal(str(predicted)), None, False, False)
        except InvalidOperation:
            return NumericalScore(False, "invalid_prediction")

    gq = parse_quantity(gold.gold_answer) if isinstance(gold.gold_answer, str) else None
    if gold.gold_value_numeric is not None:
        try:
            g_value = Decimal(str(gold.gold_value_numeric))
        except InvalidOperation:
            return NumericalScore(False, "gold_invalid")
        if gq is not None and gq.value != g_value:
            return NumericalScore(False, "gold_ambiguous_numeric_vs_text")
    elif gq is not None:
        g_value = gq.value
    else:
        return NumericalScore(False, "gold_not_numeric")
    g_scale = (gq.scale_power10 or 0) if gq else 0
    g_percent = bool(gq and gq.is_percent)
    expected_currency = gold.currency or (gq.currency if gq else None)
    expected_unit = gold.unit or (gq.unit if gq else None)
    if pq.currency == "AMBIGUOUS" or (expected_currency and pq.currency not in (None, expected_currency)):
        return NumericalScore(False, "incompatible_currency")
    if expected_currency and pq.unit == "shares":
        return NumericalScore(False, "incompatible_unit")
    if expected_unit and pq.unit and pq.unit != expected_unit:
        return NumericalScore(False, "incompatible_unit")
    if expected_unit in {"percent", "percentage_points"} and (pq.has_currency or pq.currency):
        return NumericalScore(False, "incompatible_currency")
    if gold.period_end and isinstance(predicted, str):
        declared = re.findall(r"\b\d{4}-\d{2}-\d{2}\b", predicted)
        years = re.findall(r"(?:\bFY\s*|\bfiscal\s+(?:year\s+)?|\bin\s+)((?:19|20)\d{2})\b", predicted, re.I)
        if ((declared and any(p != gold.period_end for p in declared))
                or (years and any(y != gold.period_end[:4] for y in years))):
            return NumericalScore(False, "incompatible_period")
    if not all(v.is_finite() for v in (pq.value, g_value)):
        return NumericalScore(False, "nonfinite_quantity")
    if not (0 <= gold.relative_tolerance <= 0.01 and gold.zero_tolerance >= 0):
        return NumericalScore(False, "invalid_tolerance")

    if g_percent and (pq.scale_power10 is not None or pq.has_currency or pq.currency):
        return NumericalScore(False, "wrong_unit_percent_expected")
    if not g_percent and pq.is_percent:
        return NumericalScore(False, "wrong_unit_percent_unexpected")

    inherited = pq.scale_power10 is None and not g_percent
    p_scale = 0 if g_percent else (g_scale if pq.scale_power10 is None else pq.scale_power10)
    pred_norm = pq.value.scaleb(p_scale)
    gold_norm = g_value.scaleb(0 if g_percent else g_scale)

    if g_value == 0:
        tol = Decimal(str(gold.zero_tolerance)).scaleb(0 if g_percent else g_scale)
        ok = abs(pred_norm) <= tol
        return NumericalScore(ok, "zero_gold_within_declared_tolerance" if ok else "zero_gold_outside_tolerance",
                              pred_norm, gold_norm, None, inherited)
    rel = abs(pred_norm - gold_norm) / abs(gold_norm)
    ok = rel <= Decimal(str(gold.relative_tolerance))
    return NumericalScore(ok, "within_relative_tolerance" if ok else "outside_relative_tolerance",
                          pred_norm, gold_norm, rel, inherited)


def evaluate_numerical_match(
    predicted_val: Decimal | float | int | str | None,
    gold: GoldReference,
) -> bool:
    """Boolean wrapper around :func:`score_numerical`."""
    return score_numerical(predicted_val, gold).correct


# ---------------------------------------------------------------------------
# Text scoring (F29)
# ---------------------------------------------------------------------------
def normalize_text(text: str) -> str:
    """Normalize text for matching: lowercase, strip punctuation, collapse whitespace."""
    lower = text.lower()
    no_punct = re.sub(r"[^\w\s]", " ", lower)
    return " ".join(no_punct.split())


def _gold_spans(gold: GoldReference) -> list[str]:
    spans = gold.gold_answer if isinstance(gold.gold_answer, list) else [gold.gold_answer]
    return [normalize_text(str(s)) for s in spans if str(s).strip()]


def _contains_tokens(haystack: list[str], needle: list[str]) -> bool:
    n = len(needle)
    return n > 0 and any(haystack[i:i + n] == needle for i in range(len(haystack) - n + 1))


def evaluate_text_match(predicted: str, gold: GoldReference) -> bool:
    """Named rubric 'all_gold_spans_contained': every gold span must appear as whole tokens.

    A multi-span gold such as [Products, Services] is NOT satisfied by 'Products' alone.
    This is a reviewed rubric, not official exact match; see :func:`evaluate_exact_match`.
    """
    if not isinstance(predicted, str) or not predicted.strip():
        return False
    pred_tokens = normalize_text(predicted).split()
    spans = _gold_spans(gold)
    return bool(spans) and all(_contains_tokens(pred_tokens, s.split()) for s in spans)


def evaluate_exact_match(predicted: str, gold: GoldReference) -> bool:
    """Strict normalized string equality (single span) or equality with the joined spans."""
    if not isinstance(predicted, str) or not predicted.strip():
        return False
    spans = _gold_spans(gold)
    if not spans:
        return False
    pred = normalize_text(predicted)
    if len(spans) == 1:
        return pred == spans[0]
    return sorted(pred.split()) == sorted(" ".join(spans).split())


def token_f1(predicted: str, gold: GoldReference) -> float:
    """SQuAD-style token F1 against the joined gold spans."""
    if not isinstance(predicted, str):
        return 0.0
    p, g = normalize_text(predicted).split(), " ".join(_gold_spans(gold)).split()
    if not p or not g:
        return 0.0
    remaining, common = list(g), 0
    for tok in p:
        if tok in remaining:
            remaining.remove(tok)
            common += 1
    if common == 0:
        return 0.0
    precision, recall = common / len(p), common / len(g)
    return 2 * precision * recall / (precision + recall)


# ---------------------------------------------------------------------------
# Retrieval scoring
# ---------------------------------------------------------------------------
def evaluate_retrieval(
    ranked_evidence_ids: list[str],
    gold_evidence_ids: tuple[str, ...],
) -> tuple[float, float, float, bool]:
    """Calculate Recall@5, Recall@10, MRR, and complete evidence presence.

    Returns (recall@5, recall@10, mrr, complete_evidence_bool). Retrieval@10 uses the
    pre-context ranking supplied by the caller.
    """
    if not gold_evidence_ids:
        return 0.0, 0.0, 0.0, True

    gold_set = set(gold_evidence_ids)
    top_5 = ranked_evidence_ids[:5]
    top_10 = ranked_evidence_ids[:10]

    r5 = len(set(top_5) & gold_set) / len(gold_set)
    r10 = len(set(top_10) & gold_set) / len(gold_set)

    mrr = 0.0
    for rank, eid in enumerate(ranked_evidence_ids, start=1):
        if eid in gold_set:
            mrr = 1.0 / rank
            break

    return r5, r10, mrr, gold_set.issubset(set(top_5))


# ---------------------------------------------------------------------------
# Lexical diagnostic (NOT RAGAS) (F30)
# ---------------------------------------------------------------------------
_UP = frozenset({"increase", "increased", "increases", "rose", "rise", "grew", "growth", "higher", "up", "gained", "improved"})
_DOWN = frozenset({"decrease", "decreased", "decreases", "fell", "fall", "declined", "decline", "dropped", "lower", "down", "reduced", "lost"})
_NUM_IN_TEXT = re.compile(r"(?<![\w.])\d[\d,]*(?:\.\d+)?")


def _numbers(text: str) -> set[Decimal]:
    out = set()
    for m in _NUM_IN_TEXT.finditer(text):
        try:
            out.add(Decimal(m.group(0).replace(",", "")).normalize())
        except InvalidOperation:
            pass
    return out


def _direction(tokens: list[str]) -> str | None:
    up, down = any(t in _UP for t in tokens), any(t in _DOWN for t in tokens)
    return "up" if up and not down else "down" if down and not up else None


def lexical_overlap_diagnostic(answer_text: str, evidence_blocks: list[str]) -> float:
    """Fraction of answer sentences with word overlap, number support and no direction conflict.

    DIAGNOSTIC ONLY. This is not RAGAS faithfulness and not entailment: it checks (1) at
    least half of the content words occur in the evidence, (2) every number in the sentence
    occurs in the evidence and (3) the best-overlapping evidence sentence does not state the
    opposite direction (increase vs decrease). Paraphrases and subtler contradictions are
    still invisible to it, which is why it must never be reported as RAGAS.
    """
    if not isinstance(answer_text, str) or not answer_text.strip() or not evidence_blocks:
        return 0.0
    context = " ".join(evidence_blocks)
    context_words = set(normalize_text(context).split())
    context_numbers = _numbers(context)
    context_sentences = [s for s in re.split(r"(?<=[.!?])\s+|\n", context) if s.strip()]
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", answer_text) if len(s.strip()) > 3]
    if not sentences:
        return 0.0

    grounded = 0
    for sent in sentences:
        tokens = normalize_text(sent).split()
        content = [w for w in tokens if len(w) > 3 or w in _UP or w in _DOWN]
        if not content or sum(w in context_words for w in content) / len(content) < 0.5:
            continue
        if not _numbers(sent) <= context_numbers:
            continue
        s_dir = _direction(tokens)
        if s_dir:
            best = max(context_sentences, key=lambda cs: len(set(normalize_text(cs).split()) & set(tokens)),
                       default="")
            c_dir = _direction(normalize_text(best).split())
            if c_dir and c_dir != s_dir:
                continue
        grounded += 1
    return grounded / len(sentences)


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------
@dataclass
class EvaluatorMetrics:
    total_cases: int = 0
    eligible_cases: int | None = None
    scored_cases: int = 0
    unscored_cases: int = 0
    successful_cases: int = 0
    failed_cases: int = 0
    refused_cases: int = 0
    numerical_correct: int = 0
    numerical_total: int = 0
    exact_match_correct: int = 0
    span_containment_correct: int = 0
    text_total: int = 0
    f1_scores: list[float] = field(default_factory=list)
    recall_at_5_sum: float = 0.0
    recall_at_10_sum: float = 0.0
    mrr_sum: float = 0.0
    retrieval_cases: int = 0
    complete_evidence_count: int = 0
    lexical_diagnostic_scores: list[float] = field(default_factory=list)
    ragas_scores: list[float] = field(default_factory=list)
    ragas_config: dict[str, Any] | None = None
    latencies: list[float] = field(default_factory=list)
    failure_reasons: dict[str, int] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        """Compute aggregated summary; undefined measures are None, never 0 or 1."""
        def ratio(a: float, b: float) -> float | None:
            return round(a / b, 4) if b > 0 else None

        sorted_lat = sorted(self.latencies)
        median_lat = None
        if sorted_lat:
            mid = len(sorted_lat) // 2
            median_lat = sorted_lat[mid] if len(sorted_lat) % 2 else (sorted_lat[mid - 1] + sorted_lat[mid]) / 2

        if self.ragas_scores and self.ragas_config:
            ragas = {"status": "executed", "mean": round(sum(self.ragas_scores) / len(self.ragas_scores), 4),
                     "cases": len(self.ragas_scores), "evaluator_config": self.ragas_config}
        else:
            ragas = {"status": "BLOCKED",
                     "reason": "No pinned RAGAS evaluator/model was executed with exact included contexts."}

        return {
            "total_cases": self.total_cases,
            "eligible_cases": self.eligible_cases,
            "scored_cases": self.scored_cases,
            "unscored_cases": self.unscored_cases,
            "successful_cases": self.successful_cases,
            "failed_cases": self.failed_cases,
            "refused_cases": self.refused_cases,
            "numerical_accuracy": ratio(self.numerical_correct, self.numerical_total),
            "numerical_cases": self.numerical_total,
            "exact_match_accuracy": ratio(self.exact_match_correct, self.text_total),
            "span_containment_accuracy": ratio(self.span_containment_correct, self.text_total),
            "token_f1_mean": round(sum(self.f1_scores) / len(self.f1_scores), 4) if self.f1_scores else None,
            "text_cases": self.text_total,
            "recall_at_5": ratio(self.recall_at_5_sum, self.retrieval_cases),
            "recall_at_10": ratio(self.recall_at_10_sum, self.retrieval_cases),
            "mrr": ratio(self.mrr_sum, self.retrieval_cases),
            "complete_evidence_rate": ratio(self.complete_evidence_count, self.retrieval_cases),
            "retrieval_cases": self.retrieval_cases,
            "lexical_overlap_diagnostic_mean": (
                round(sum(self.lexical_diagnostic_scores) / len(self.lexical_diagnostic_scores), 4)
                if self.lexical_diagnostic_scores else None),
            "lexical_overlap_diagnostic_note": "Heuristic only; not RAGAS and not entailment.",
            "ragas_faithfulness": ragas,
            "median_latency_seconds": round(median_lat, 3) if median_lat is not None else None,
            "mean_latency_seconds": round(sum(sorted_lat) / len(sorted_lat), 3) if sorted_lat else None,
            "failure_reasons": dict(self.failure_reasons),
        }


def _is_numeric_gold(gold: GoldReference) -> bool:
    if gold.gold_value_numeric is not None:
        return True
    return isinstance(gold.gold_answer, str) and parse_quantity(gold.gold_answer) is not None


def compute_all_metrics(
    eval_results: list[dict[str, Any]],
    gold_refs: dict[str, GoldReference],
    eligible_cases: int | None = None,
    ragas_scores: list[float] | None = None,
    ragas_config: dict[str, Any] | None = None,
) -> EvaluatorMetrics:
    """Compute the metric suite across all evaluation results.

    ``eligible_cases`` is the full eligible denominator (not the processed subset) so a
    max_cases pilot can never masquerade as full coverage. Results lacking a gold
    reference are counted as unscored, not silently dropped.
    """
    m = EvaluatorMetrics(total_cases=len(eval_results), eligible_cases=eligible_cases,
                         ragas_scores=list(ragas_scores or []), ragas_config=ragas_config)

    for res in eval_results:
        gold = gold_refs.get(res["case_id"])
        if gold is None:
            m.unscored_cases += 1
            continue
        m.scored_cases += 1

        status = res.get("status", "unknown")
        if "latency_seconds" in res:
            m.latencies.append(float(res["latency_seconds"]))

        if status == "ok":
            m.successful_cases += 1
        elif status in {"insufficient_evidence", "invalid_request", "index_not_ready"}:
            m.refused_cases += 1
            reason = res.get("message") or status
            m.failure_reasons[reason] = m.failure_reasons.get(reason, 0) + 1
        else:
            m.failed_cases += 1
            reason = res.get("message") or status
            m.failure_reasons[reason] = m.failure_reasons.get(reason, 0) + 1

        ranked_ids = res.get("ranked_evidence_ids", res.get("included_evidence_ids", []))
        if gold.gold_evidence_ids:
            r5, r10, mrr, complete = evaluate_retrieval(ranked_ids, gold.gold_evidence_ids)
            m.recall_at_5_sum += r5
            m.recall_at_10_sum += r10
            m.mrr_sum += mrr
            m.complete_evidence_count += int(complete)
            m.retrieval_cases += 1

        pred_ans = res.get("answer", "")
        if _is_numeric_gold(gold):
            m.numerical_total += 1
            if status == "ok" and evaluate_numerical_match(pred_ans, gold):
                m.numerical_correct += 1
        else:
            m.text_total += 1
            if status == "ok":
                m.exact_match_correct += int(evaluate_exact_match(pred_ans, gold))
                m.span_containment_correct += int(evaluate_text_match(pred_ans, gold))
                m.f1_scores.append(token_f1(pred_ans, gold))
            else:
                m.f1_scores.append(0.0)

        evidence_texts = [e.get("content", "") for e in res.get("evidence", []) if isinstance(e, dict)]
        if status == "ok" and pred_ans:
            m.lexical_diagnostic_scores.append(lexical_overlap_diagnostic(pred_ans, evidence_texts))

    return m


def compute_paired_intervals(
    scores_a: list[float],
    scores_b: list[float],
    n_bootstrap: int = 10_000,
    seed: int = 42,
) -> tuple[float, float]:
    """95% percentile bootstrap interval for mean(scores_a - scores_b), pairing by question.

    Raises ValueError for empty or unpaired inputs rather than returning a fabricated (0, 0).
    """
    if not scores_a or len(scores_a) != len(scores_b):
        raise ValueError("Paired intervals need equal-length, non-empty score lists.")

    rng = random.Random(seed)
    n = len(scores_a)
    diffs = [a - b for a, b in zip(scores_a, scores_b)]
    means = sorted(sum(diffs[rng.randrange(n)] for _ in range(n)) / n for _ in range(n_bootstrap))
    lower = means[int(0.025 * n_bootstrap)]
    upper = means[min(n_bootstrap - 1, int(0.975 * n_bootstrap))]
    return round(lower, 4), round(upper, 4)
