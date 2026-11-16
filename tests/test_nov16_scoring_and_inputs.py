"""F29/F30/F33/F26 (R7/R12): unit-normalized scoring, honest faithfulness, leakage-free inputs.

Viva: why must units be normalized before applying a relative-error threshold, and why does
shared vocabulary fail to establish entailment?
"""

import json

import pytest

from src.benchmark.loaders import (
    BenchmarkInputError,
    GoldReference,
    _parse_raw_record,
    assess_suite_provenance,
    find_forbidden_keys,
    load_benchmark,
    verify_gold_separation,
)
from src.benchmark.metrics import (
    compute_all_metrics,
    compute_paired_intervals,
    evaluate_exact_match,
    evaluate_numerical_match,
    evaluate_text_match,
    lexical_overlap_diagnostic,
    score_numerical,
    token_f1,
)


def gold(answer="100 million USD", numeric=100.0, **kw):
    return GoldReference(case_id="G", benchmark="T", gold_answer=answer, gold_value_numeric=numeric, **kw)


# ---- F29 numerical: positive controls ------------------------------------------------------
@pytest.mark.parametrize("pred", ["100 million USD", "$100M", "0.1 billion USD", "100.5 million USD",
                                  "Fiscal 2021 revenue was $100 million", "100"])
def test_equivalent_scale_and_within_one_percent_pass(pred):
    assert evaluate_numerical_match(pred, gold())


def test_plain_100_vs_100_passes_and_102_vs_100_fails():
    plain = GoldReference(case_id="p", benchmark="t", gold_answer="100", gold_value_numeric=100.0)
    assert evaluate_numerical_match("100", plain)
    assert not evaluate_numerical_match("102", plain)


# ---- F29 numerical: failures -----------------------------------------------------------------
@pytest.mark.parametrize("pred", ["100 billion USD", "100 thousand USD", "102 million USD", "50%", "no number"])
def test_wrong_scale_wrong_value_or_wrong_unit_fail(pred):
    assert not evaluate_numerical_match(pred, gold())


def test_gold_numeric_is_in_the_display_unit_of_the_gold_text():
    tat = gold("45,000 million USD", 45000.0)
    assert evaluate_numerical_match("45 billion USD", tat)
    assert not evaluate_numerical_match("45 million USD", tat)
    assert score_numerical("45 billion USD", tat).gold_normalized == 45_000_000_000


def test_percent_gold_rejects_scaled_or_currency_predictions():
    pct = gold("20.02%", 20.02)
    assert evaluate_numerical_match("20.1%", pct) and not evaluate_numerical_match("20.02 million", pct)
    assert not evaluate_numerical_match("$20.02", pct)
    assert not evaluate_numerical_match("20.02%", gold("20.02 million USD", 20.02))


def test_zero_gold_uses_declared_tolerance_in_display_unit():
    zero = gold("0.00", 0.0, zero_tolerance=0.001)
    assert evaluate_numerical_match("0.0005", zero) and not evaluate_numerical_match("0.05", zero)


def test_inconsistent_gold_is_not_silently_scored():
    assert score_numerical("100 million", gold("100 million USD", 500.0)).reason == "gold_ambiguous_numeric_vs_text"


# ---- F29 text ---------------------------------------------------------------------------------
def test_multi_span_gold_needs_every_span():
    multi = GoldReference(case_id="m", benchmark="t", gold_answer=["Products", "Services"])
    assert not evaluate_text_match("Products only.", multi)
    assert evaluate_text_match("Products and Services", multi)
    assert not evaluate_text_match("Productsfoo and Servicesbar", multi)  # whole tokens, not substrings


def test_exact_match_and_f1_are_reported_separately_from_containment():
    single = GoldReference(case_id="s", benchmark="t", gold_answer="Services Segment")
    assert evaluate_text_match("The revenue came from the services segment.", single)
    assert not evaluate_exact_match("The revenue came from the services segment.", single)
    assert evaluate_exact_match("services segment", single)
    assert 0 < token_f1("The revenue came from the services segment.", single) < 1


def test_summary_reports_undefined_measures_as_none_and_ragas_blocked():
    m = compute_all_metrics([], {}, eligible_cases=150).summary()
    assert m["numerical_accuracy"] is None and m["recall_at_5"] is None and m["median_latency_seconds"] is None
    assert m["eligible_cases"] == 150
    assert m["ragas_faithfulness"]["status"] == "BLOCKED"
    assert "faithfulness_mean" not in m


def test_results_without_gold_are_counted_unscored_not_dropped():
    m = compute_all_metrics([{"case_id": "?", "status": "ok"}], {}, eligible_cases=1)
    assert m.unscored_cases == 1 and m.scored_cases == 0


def test_paired_intervals_reject_unpaired_and_default_to_10000_resamples():
    with pytest.raises(ValueError):
        compute_paired_intervals([], [])
    with pytest.raises(ValueError):
        compute_paired_intervals([1.0], [1.0, 2.0])
    import inspect
    assert inspect.signature(compute_paired_intervals).parameters["n_bootstrap"].default == 10_000


# ---- F30 -----------------------------------------------------------------------------------------
def test_lexical_diagnostic_supported_statement_scores_full():
    assert lexical_overlap_diagnostic("Revenue increased significantly.", ["Revenue increased significantly."]) == 1.0


def test_lexical_diagnostic_rejects_contradiction_and_unsupported_numbers():
    assert lexical_overlap_diagnostic("Revenue decreased significantly.", ["Revenue increased significantly."]) == 0.0
    assert lexical_overlap_diagnostic("Revenue was 999 USD.", ["Revenue was 100 USD."]) == 0.0


# ---- F33 -----------------------------------------------------------------------------------------
def record(**extra):
    base = {"case_id": "C1", "benchmark": "FinanceBench", "question": "What was revenue?",
            "company": "Apple Inc.", "fiscal_year": "2021", "context_text": ["Revenue was 100."],
            "context_tables": [{"table_title": "T", "rows": [["Revenue", "100"]]}],
            "gold": {"gold_answer": "100"}}
    base.update(extra)
    return base


def test_clean_record_parses_and_keeps_gold_only_in_reference():
    case, ref = _parse_raw_record(record())
    assert ref.gold_answer == "100" and verify_gold_separation(case.to_eval_input())
    assert "gold" not in json.dumps(case.to_eval_input())


@pytest.mark.parametrize("bad", [
    {"gold_answer": "SECRET"},                                                   # raw top-level target
    {"metadata": {"gold_answer": "SECRET"}},                                     # nested in metadata
    {"context_tables": [{"table_title": "T", "rows": [], "label": "SECRET"}]},   # nested in a table
    {"context_text": ["ok"], "notes": {"deep": [{"Target": "SECRET"}]}},         # deep, any case
    {"unreviewed_field": 1},                                                     # not allowlisted
])
def test_nested_or_unallowlisted_targets_refuse(bad):
    with pytest.raises(BenchmarkInputError):
        _parse_raw_record(record(**bad))


def test_find_forbidden_keys_is_recursive_and_case_insensitive():
    assert find_forbidden_keys({"a": [{"b": {"Gold_Answer": 1}}]}) == ["/a[0]/b/Gold_Answer"]
    assert verify_gold_separation({"metadata": {"deep": {"program": "x"}}}) is False


# ---- F26 -----------------------------------------------------------------------------------------
def test_committed_fixtures_are_classified_synthetic_and_quantified():
    fb = assess_suite_provenance(load_benchmark("FinanceBench"))
    assert fb["records"] == 150 and fb["classification"] == "synthetic_smoke_fixture"
    assert fb["full_evaluation_eligible"] is False and fb["authentic_source_bound_records"] == 0
    # Count agreement is not validity: 150 records share a single generated context.
    assert fb["unique_contexts"] < 150 and fb["unique_gold_answers"] < 150
    assert assess_suite_provenance(load_benchmark("FinQA"))["unique_questions"] == 20
    assert assess_suite_provenance(load_benchmark("TAT-QA"))["full_evaluation_eligible"] is False


def test_complete_official_provenance_is_required_for_authentic_classification():
    prov = {"official_dataset": "FinanceBench", "official_id": "financebench_id_00001", "official_version": "open-150",
            "split": "open", "license": "CC-BY-NC-4.0", "source_sha256": "a" * 64}
    case, _ = _parse_raw_record(record(provenance=prov))
    assert case.provenance_class == "authentic_source_bound"
    partial = dict(prov)
    del partial["source_sha256"]
    assert _parse_raw_record(record(provenance=partial))[0].provenance_class == "synthetic_smoke_fixture"
