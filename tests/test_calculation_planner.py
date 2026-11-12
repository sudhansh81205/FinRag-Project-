import json
from types import SimpleNamespace

from src.llm.calculation_planner import propose_calculation
from tests.test_typed_calculator import fact, leaf, op, plan


def client(expression):
    return SimpleNamespace(provider='ollama', model='gemma3:4b', expected_digest='a'*64,
                           generate=lambda *a, **k: {'status':'ok','provider':'ollama','model':'gemma3:4b',
                               'model_fingerprint':{'digest':'a'*64}, 'text':json.dumps({'expression':expression})})


def request():
    return {k:v for k,v in plan(leaf('x')).items() if k != 'expression'}


def test_planner_cannot_inject_numeric_values_or_python():
    records = [fact('x', 10), fact('y', 5)]
    result = propose_calculation('Difference?', request(), records, client(op('subtract',leaf('x'),leaf('y'))))
    assert result['status'] == 'ok' and result['result'] == '5000000'
    result = propose_calculation('Difference?', request(), records, client({'python':'open(secret).read()'}))
    assert result['status'] == 'rule_failure'
    result = propose_calculation('Difference?', request(), records, client({'evidence_id':'x','value':999}))
    assert result['status'] == 'rule_failure'


def test_planner_cannot_change_request_period_or_choose_absent_evidence():
    result = propose_calculation('Difference?', request(), [fact('x',10,2020)], client(leaf('x')))
    assert result['error_code'] == 'requested_period'
    result = propose_calculation('Difference?', request(), [fact('x',10)], client(leaf('missing')))
    assert result['error_code'] == 'included_citation'
