"""R5 live-discovered regression: valid arithmetic can express the wrong metric."""

import copy
import hashlib

from src.application import make_demo_records
from src.llm.financial_semantics import known_source_program, validate_named_formula
from src.llm.typed_calculator import evaluate


def facts_and_request():
    revenue, gross = copy.deepcopy(make_demo_records())
    gross["evidence_id"] = "gross-profit"
    gross["content"] = "Apple | Gross profit | FY2021 | 152836 USD millions"
    gross["metadata"].update(metric="us-gaap:GrossProfit", raw_value="152836",
                             normalized_value_decimal="152836000000", normalized_value=152836000000,
                             content_sha256=hashlib.sha256(gross["content"].encode()).hexdigest())
    m = revenue["metadata"]
    request = {"issuer": "Apple Inc.", "scope": "consolidated",
               "periods": [{"kind": m["period_kind"], "start": m["period_start"], "end": m["period_end"]}]}
    return [revenue, gross], request


def test_wrong_gross_margin_formula_is_refused_even_when_arithmetic_and_units_pass():
    records, request = facts_and_request()
    revenue, gross = {"evidence_id": "sales"}, {"evidence_id": "gross-profit"}
    program = {**request, "expression": {"op": "ratio_percent", "args": [
        {"op": "subtract", "args": [gross, revenue]}, revenue]}}
    assert evaluate(program, records)["status"] == "ok"  # the previously missed semantic gap
    assert validate_named_formula("What was gross margin percentage?", program, records)


def test_known_formula_uses_actual_included_gross_profit_and_revenue_without_constants():
    records, request = facts_and_request()
    program = known_source_program("What was gross margin in FY2021?", request, records)
    assert validate_named_formula("Gross margin percentage?", program, records) == ""
    result = evaluate(program, records)
    assert result["status"] == "ok"
    assert round(float(result["result"]), 2) == 41.78
    assert set(result["operand_ids"]) == {"sales", "gross-profit"}


def test_missing_foreign_or_ambiguous_revenue_cannot_create_a_formula():
    records, request = facts_and_request()
    assert known_source_program("gross margin?", request, records[1:]) is None
    assert known_source_program("gross margin?", {**request, "issuer": "Microsoft"}, records) is None
    duplicate = copy.deepcopy(records[0])
    duplicate["evidence_id"] = "other-revenue"
    assert known_source_program("gross margin?", request, records + [duplicate]) is None


def test_revenue_minus_cost_is_valid_but_reversed_subtraction_is_not():
    records = make_demo_records()
    m = records[0]["metadata"]
    request = {"issuer": "Apple Inc.", "scope": "consolidated",
               "periods": [{"kind": m["period_kind"], "start": m["period_start"], "end": m["period_end"]}]}
    program = known_source_program("gross margin?", request, records)
    assert validate_named_formula("gross margin?", program, records) == ""
    program["expression"]["args"][0]["args"].reverse()
    assert validate_named_formula("gross margin?", program, records)


def test_margin_change_cannot_be_answered_with_a_single_period_level():
    records, request = facts_and_request()
    level = known_source_program('What was gross margin?', request, records)
    for question in ('What was the change in gross margin?', 'How did gross margin compare versus last year?'):
        assert known_source_program(question, request, records) is None
        assert validate_named_formula(question, level, records)


def test_interactive_margin_expansion_preserves_question_and_source_checks():
    from src.pipeline.finrag_engine import FinRAGEngine

    records, request = facts_and_request()
    queries = []

    class Retriever:
        def retrieve(self, **kwargs):
            queries.append(kwargs)
            return {"all_evidence": records, "ranking_applied": True}

    class Client:
        provider, model = "ollama", "test-fixture"

        def generate(self, prompt):
            assert "what was Apple's gross margin in fy2021" in prompt
            return {"success": True, "status": "ok", "provider": self.provider,
                    "model": self.model, "text": "fixture explanation"}

    engine = FinRAGEngine(retriever=Retriever(), llm_client=Client())
    question = "what was Apple's gross margin in fy2021"
    result = engine.answer_financial_question(question, calculation_request=request,
                                              expand_named_metric=True)
    assert result["status"] == "ok"
    assert result["question"] == question
    assert round(float(result["calculations"][0]["result"]), 2) == 41.78
    assert queries[-1]["query"] == "gross profit total net sales revenue cost of sales"
    engine.answer_financial_question(question, calculation_request=request)
    assert queries[-1]["query"] == question  # matched experiment defaults unchanged


def test_interactive_typed_lookup_uses_only_selected_filing_operands():
    import copy

    from src.pipeline.finrag_engine import FinRAGEngine

    records, request = facts_and_request()
    records[0]['metadata']['row_headers'] = ['Total net sales']
    for record in records:
        record['metadata']['accession'] = 'selected-filing'
    foreign = copy.deepcopy(records[0])
    foreign['evidence_id'] = 'foreign-sales'
    foreign['metadata']['accession'] = 'other-filing'

    class Retriever:
        def retrieve(self, **kwargs):
            raise AssertionError('Named typed lookup must not depend on a lexical shortlist')

    class Client:
        provider, model = 'ollama', 'fixture'
        def generate(self, prompt):
            return {'success': True, 'status': 'ok', 'provider': self.provider,
                    'model': self.model, 'text': 'fixture'}

    engine = FinRAGEngine(retriever=Retriever(), llm_client=Client())
    engine.web_source_records = records + [foreign]
    result = engine.answer_financial_question("what was Apple's gross margin in fy2021",
        calculation_request=request, filters={'accession': 'selected-filing'}, expand_named_metric=True)
    assert result['status'] == 'ok'
    assert 'foreign-sales' not in result['included_evidence_ids']
    assert round(float(result['calculations'][0]['result']), 2) == 41.78
    engine.web_source_records = records[1:]
    result = engine.answer_financial_question('gross margin?', calculation_request=request,
        filters={'accession': 'selected-filing'}, expand_named_metric=True)
    assert result['status'] == 'insufficient_evidence' and not result['answer']
