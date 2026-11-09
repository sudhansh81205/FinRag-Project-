"""R5 success and refusal fixtures, including actual selected-context binding."""

import copy
import hashlib
from decimal import Decimal

import pytest

from src.llm.typed_calculator import evaluate
from src.pipeline.finrag_engine import FinRAGEngine


def fact(identity, value, year=2021, metric="Revenue", **changes):
    content = f"Apple Inc. | {metric} | {year} | {value} | USD millions"
    return {"evidence_id": identity, "content": content, "metadata": {
        "type": "table_cell", "company": "Apple Inc.", "metric": metric,
        "scope": "consolidated", "table_title": "Statement of Operations",
        "source_url": "https://www.sec.gov/example", "source_locator": "table tr td",
        "accession": "fixture-not-live", "content_sha256": hashlib.sha256(content.encode()).hexdigest(),
        "period_kind": "duration", "period_start": f"{year-1}-09-27", "period_end": f"{year}-09-25",
        "normalized_unit": "USD", "unit": "USD", "currency": "USD", "scale": 1000000,
        "scale_power10": 6, "raw_value": str(value), "raw_unit": "millions",
        "normalized_value_decimal": str(value * 1000000), "normalized_value": value * 1000000,
        **changes}}


def leaf(identity):
    return {"evidence_id": identity}


def op(name, left, right):
    return {"op": name, "args": [left, right]}


def plan(expression, years=(2021,)):
    return {"issuer": "Apple Inc.", "scope": "consolidated", "expression": expression,
            "periods": [{"kind": "duration", "start": f"{y-1}-09-27", "end": f"{y}-09-25"} for y in years]}


def test_multistep_margin_and_trace():
    records = [fact("sales", 365817), fact("cost", 212981, metric="CostOfSales")]
    result = evaluate(plan(op("ratio_percent", op("subtract", leaf("sales"), leaf("cost")), leaf("sales"))), records)
    assert result["status"] == "ok"
    assert abs(Decimal(result["result"]) - Decimal('41.7794')) < Decimal('.0001')
    assert result["unit"] == "percent" and result["operand_ids"] == ["sales", "cost"]
    assert result["rule_trace"][-1]["rule_id"] == "ratio_percent"
    assert result["operands"]["sales"]["raw_value"] == "365817"


@pytest.mark.parametrize("prior,expected,unit", [(274515, "33.259", "percent"), (-10, "365827000000", "USD")])
def test_growth_policy(prior, expected, unit):
    result = evaluate(plan(op("percent_change", leaf("now"), leaf("before")), (2021, 2020)),
                      [fact("now", 365817), fact("before", prior, 2020)])
    assert result["status"] == "ok" and result["unit"] == unit
    if prior > 0:
        assert abs(Decimal(result["result"]) - Decimal(expected)) < Decimal('.001')
    else:
        assert result["result"] == expected
        assert "Negative prior" in result["rule_trace"][-1]["note"]


@pytest.mark.parametrize("field,value,rule", [
    ("company", "Microsoft", "issuer_scope"), ("scope", "segment", "issuer_scope"),
    ("normalized_unit", "EUR", "unit"), ("currency", "EUR", "currency"),
    ("scale", 1, "scale"), ("normalized_value_decimal", "42", "normalization"),
    ("raw_value", "—", "raw_value"), ("content_sha256", "wrong", "content_integrity"),
    ("source_locator", "", "fact_identity"), ("period_end", "2020-09-25", "period"),
])
def test_incompatible_or_untraceable_fact_refused(field, value, rule):
    f = fact("x", 50, **{field: value})
    assert evaluate(plan(leaf("x")), [f])["error_code"] == rule


def test_missing_ambiguous_zero_and_code_refused():
    f = fact("x", 0)
    assert evaluate(plan(leaf("missing")), [f])["error_code"] == "included_citation"
    assert evaluate(plan(leaf("x")), [f, f])["error_code"] == "unique_citation"
    assert evaluate(plan(op("divide", leaf("x"), leaf("x"))), [f])["error_code"] == "nonzero_denominator"
    assert evaluate(plan({"op": "__import__", "args": [leaf("x"), leaf("x")]}), [f])["error_code"] == "allowed_operation"
    assert evaluate(plan({"evidence_id": "x", "value": "999"}), [f])["error_code"] == "allowed_operation"


def test_wrong_period_metric_and_tree_bounds_refused():
    records = [fact("now", 50), fact("before", 20, 2020, metric="Cost")]
    p = plan(op("percent_change", leaf("now"), leaf("before")), (2021, 2020))
    assert evaluate(p, records)["error_code"] == "comparable_metric"
    p["expression"] = op("subtract", leaf("now"), leaf("before"))
    assert evaluate(p, records)["error_code"] == "same_period"
    tree = leaf("now")
    for _ in range(9):
        tree = op("add", tree, leaf("now"))
    assert evaluate(plan(tree), records)["error_code"] == "bounded_tree"
    assert evaluate(plan(leaf("before")), records)["error_code"] == "requested_period"


def test_ratio_times_money_multistep():
    result = evaluate(plan(op("multiply", op("divide", leaf("x"), leaf("y")), leaf("y"))),
                      [fact("x", 10), fact("y", 20)])
    assert result["status"] == "ok" and result["result"] == "10000000.0" and result["unit"] == "USD"


class SourceRetriever:
    def retrieve(self, **kwargs):
        return {"text_evidence": [], "table_evidence": [fact("sales", 365817), fact("cost", 212981, metric="Cost")]}


class PreserveRank:
    def rerank(self, **kwargs):
        return kwargs["candidates"][:kwargs["top_n"]]


class ProviderSpy:
    provider, model = "ollama", "test-spy"
    calls = 0

    def generate(self, prompt):
        self.calls += 1
        assert "Validated calculator" in prompt
        return {"provider": self.provider, "model": self.model, "status": "ok", "success": True, "text": "Fixture explanation"}


def test_engine_calculates_only_after_actual_context_selection():
    spy = ProviderSpy()
    engine = FinRAGEngine(SourceRetriever(), PreserveRank(), spy)
    p = plan(op("subtract", leaf("sales"), leaf("cost")))
    result = engine.answer_financial_question("Gross profit?", calculation_plan=p)
    assert result["status"] == "ok" and spy.calls == 1
    assert result["calculations"][0]["result"] == "152836000000"
    assert result["answer"].startswith("Verified result: 152836000000 USD")
    assert result["model_explanation"] == "Fixture explanation"
    # Removed by reranking -> not allowed as operand; model isn't called.
    result = engine.answer_financial_question("Gross profit?", rerank_top_n=1, calculation_plan=copy.deepcopy(p))
    assert result["status"] == "insufficient_evidence" and spy.calls == 1
    assert result["error_code"] == "included_citation" and result["answer"] == ""
