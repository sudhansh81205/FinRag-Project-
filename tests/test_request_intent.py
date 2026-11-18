import copy

import pytest

from src.application import make_demo_records
from src.config import load_settings
from src.llm.financial_semantics import known_source_program, validate_named_formula
from src.llm.typed_calculator import evaluate
from src.web_api import WebApplication
from tests.test_named_financial_formulas import facts_and_request


@pytest.mark.parametrize('question', ["What was Apple's gross margin in FY2024?", "What was Microsoft's gross margin in FY2021?", "Compare Apple and Microsoft revenue in FY2021", "What was MSFT revenue in FY2021?", "What was Tesla revenue in FY2021?", "How much revenue did Google report in FY2021?", "What was Tesla’s gross margin in FY2021?"])
def test_mismatched_question_is_refused_before_inference(question):
    class Engine:
        web_source_records = make_demo_records()
        def answer_financial_question(self, **kwargs):
            raise AssertionError('Conflicting question must not reach retrieval/model')
    r = WebApplication(load_settings(environ={}), Engine()).answer({'question': question,
        'ticker': 'AAPL', 'accession': '0000320193-21-000105', 'value_period_end': '2021-09-25',
        'scope': 'consolidated', 'period_kind': 'duration', 'mode': 'auto'})
    assert r['status'] == 'invalid_request' and r['answer'] == '' and not r['evidence']


def test_margin_comparison_uses_two_actual_periods_and_percentage_points():
    records, request = facts_and_request()
    prior = copy.deepcopy(records)
    for record in prior:
        record['evidence_id'] += '-prior'
        record['metadata'].update(period_start='2019-09-29', period_end='2020-09-26')
    current = request['periods'][0]
    request['periods'] = [current, {'kind': 'duration', 'start': '2019-09-29', 'end': '2020-09-26'}]
    program = known_source_program('What was the change in gross margin from FY2020 to FY2021?', request, records + prior)
    assert program and not validate_named_formula('change in gross margin', program, records + prior)
    calculation = evaluate(program, records + prior)
    assert calculation['status'] == 'ok' and calculation['unit'] == 'percentage points'
    assert calculation['result'] == '0.00000000000000000000000000'
    assert known_source_program('change in gross margin', request, records) is None


def test_revenue_growth_requires_matching_total_source_values():
    records, request = facts_and_request()
    records[0]['metadata']['row_headers'] = ['Total net sales']
    prior = copy.deepcopy(records[0])
    prior['evidence_id'] = 'prior-sales'
    prior['metadata'].update(period_start='2019-09-29', period_end='2020-09-26')
    request['periods'].append({'kind': 'duration', 'start': '2019-09-29', 'end': '2020-09-26'})
    p = known_source_program('What was revenue growth from FY2020 to FY2021?', request, records + [prior])
    assert p['expression']['op'] == 'percent_change'
    assert evaluate(p, records+[prior])['status'] == 'ok'


@pytest.mark.parametrize('question', ["What is Apple's stock price today?", 'Predict Apple revenue in FY2027', 'What was Apple Q1 revenue in FY2021?'])
def test_live_prediction_and_quarter_requests_refuse_before_inference(question):
    class Engine:
        web_source_records = make_demo_records()
        def answer_financial_question(self, **kwargs):
            raise AssertionError('Unsupported source must not reach inference')
    result = WebApplication(load_settings(environ={}), Engine()).answer({'question': question,
        'ticker':'AAPL','accession':'0000320193-21-000105','value_period_end':'2021-09-25',
        'scope':'consolidated','period_kind':'duration','mode':'auto'})
    assert result['status'] == 'invalid_request' and not result['answer']


def test_relative_margin_change_requires_the_relative_formula():
    records, request = facts_and_request()
    prior = copy.deepcopy(records)
    for record in prior:
        record["evidence_id"] += "-prior"
        record["metadata"].update(period_start="2019-09-29", period_end="2020-09-26")
    request["periods"].append({"kind": "duration", "start": "2019-09-29", "end": "2020-09-26"})
    sources = records + prior
    relative = "By what percentage did gross margin increase from FY2020 to FY2021?"
    points = "By how many percentage points did gross margin increase from FY2020 to FY2021?"
    program = known_source_program(relative, request, sources)
    assert evaluate(program, sources)["unit"] == "percent"
    assert not validate_named_formula(relative, program, sources)
    assert validate_named_formula(points, program, sources)
    assert validate_named_formula(relative, known_source_program(points, request, sources), sources)
