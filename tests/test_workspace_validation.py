"""R7/R12: scoring must reject period/unit/citation errors and never invent review."""
import copy

import pytest
from bs4 import BeautifulSoup

from scripts.evaluate_workspace import assess, source_check


def numeric_example():
    case = {"category": "numerical", "accession": "filing", "input": {"value_period_end": "2025-06-30"},
            "reference": {"expected_status": "ok", "value": "100", "unit": "USD", "operand_groups": [["E1"]]}}
    result = {"status": "ok", "evidence": [{"evidence_id": "E1", "metadata": {"accession": "filing"}}],
              "included_evidence_ids": ["E1"], "calculations": [{"status": "ok", "result": "100", "unit": "USD",
                    "program": {"periods": [{"end": "2025-06-30"}]}}]}
    return case, result


def test_exact_value_alone_cannot_pass_wrong_unit_period_or_citation():
    case, result = numeric_example()
    assert assess(case, result)["automated_correct"]
    for key, value in [("unit", "percent"), ("program", {"periods": [{"end": "2024-06-30"}]}), ("result", "102")]:
        changed = copy.deepcopy(result)
        changed["calculations"][0][key] = value
        assert not assess(case, changed)["automated_correct"]
    changed = copy.deepcopy(result)
    changed["included_evidence_ids"] = ["other"]
    assert not assess(case, changed)["automated_correct"]


def test_faithfulness_cannot_be_inferred_from_valid_narrative_citation_ids():
    case, result = numeric_example()
    case["category"] = "narrative_manual"
    score = assess(case, result)
    assert score["citation_identity"] is True
    assert score["automated_correct"] is None and score["manual_review"] == "pending"


def test_original_inline_value_scale_and_separate_exhibit_context_are_checked():
    source = BeautifulSoup('<ix:nonfraction id="f" name="us-gaap:Revenues" contextref="c" scale="6">10</ix:nonfraction>', "html.parser")
    context = BeautifulSoup('<xbrli:context id="c"><xbrli:period><xbrli:enddate>2025-06-30</xbrli:enddate></xbrli:period></xbrli:context>', "html.parser")
    record = {"evidence_id": "fact", "metadata": {"source_sha256": "exhibit", "context_source_sha256": "main",
              "source_locator": "#f", "metric": "us-gaap:Revenues", "context_ref": "c", "normalized_value_decimal": "10000000", "period_end": "2025-06-30"}}
    soups = {"exhibit": source, "main": context}
    assert source_check(record, soups)["normalized_value"] == "1.0E+7"
    record["metadata"]["normalized_value_decimal"] = "100"
    with pytest.raises(ValueError, match="scale"):
        source_check(record, soups)
    record["metadata"]["normalized_value_decimal"] = "10000000"
    record["metadata"]["period_end"] = "2024-06-30"
    with pytest.raises(ValueError, match="period"):
        source_check(record, soups)
