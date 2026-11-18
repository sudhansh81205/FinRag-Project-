"""Meaningful scoring boundaries: multi-operand recall and paired clustering."""
import pytest

from src.validation_metrics import clustered_interval, ranked_operand_metrics


def test_repeated_equivalent_source_does_not_double_count_an_operand():
    groups = [["revenue", "revenue-repeated"], ["prior-revenue"]]
    metrics = ranked_operand_metrics(["revenue-repeated", "other", "revenue"], groups)
    assert metrics["recall_at_5"] == 0.5 and metrics["complete_at_5"] == 0
    assert metrics["mrr_at_10"] == 1
    metrics = ranked_operand_metrics(["other", "revenue-repeated", "prior-revenue"], groups)
    assert metrics["complete_at_5"] == 1 and metrics["mrr_at_10"] == 0.5


def test_complete_at_ten_is_distinct_from_complete_at_five():
    metrics = ranked_operand_metrics(["revenue", "a", "b", "c", "d", "cost"], [["revenue"], ["cost"]])
    assert metrics["recall_at_5"] == 0.5 and metrics["recall_at_10"] == 1
    assert metrics["complete_at_5"] == 0 and metrics["complete_at_10"] == 1
    with pytest.raises(ValueError):
        ranked_operand_metrics(["same", "same"], [["same"]])


def test_clustered_interval_is_seeded_and_retains_negative_paired_effects():
    rows = [{"accession": "f1", "delta": -1}, {"accession": "f1", "delta": -1},
            {"accession": "f2", "delta": -1}]
    first = clustered_interval(rows, "delta", samples=200)
    assert first == clustered_interval(rows, "delta", samples=200)
    assert first["estimate"] == first["low"] == first["high"] == -1
    assert first["clusters"] == 2
