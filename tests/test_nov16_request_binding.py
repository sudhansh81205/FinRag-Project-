"""F27/F32/F24 (R3/R5/R6/R12): request-bound evidence, exact filing tuples, strict operands.

KR&R success: the same issuer/filing/period/scope and included cited operands license the
41.78 percent Apple margin. Failure: the identical arithmetic is refused for any request whose
premises differ. Viva: which request premises must hold before the arithmetic is licensed?
"""

import copy

import pytest

from src.application import (
    InteractiveApplication,
    load_filing_options,
    make_demo_records,
    resolve_request,
)
from src.config import load_settings
from src.pipeline.experiment_scaffold import verify_included_operands

PLAN = {
    "issuer": "Apple Inc.",
    "scope": "consolidated",
    "periods": [{"kind": "duration", "start": "2020-09-27", "end": "2021-09-25"}],
    "expression": {"op": "ratio_percent", "args": [
        {"op": "subtract", "args": [{"evidence_id": "sales"}, {"evidence_id": "cost"}]},
        {"evidence_id": "sales"}]},
}


@pytest.fixture
def app():
    return InteractiveApplication(load_settings(environ={
        "FINRAG_HOST": "127.0.0.1", "FINRAG_PORT": "7860",
        "FINRAG_PROVIDER": "unconfigured", "FINRAG_MODEL": "test-model"}))


def option(ticker, year):
    return next(o for o in load_filing_options() if o.ticker == ticker and o.filing_period_end.startswith(str(year)))


def request_for(ticker, year, value_period=None):
    o = option(ticker, year)
    req, err = resolve_request(o.label, value_period or o.filing_period_end, "consolidated")
    assert req is not None, err
    return req


# ---- F32: every option forwards its exact registry tuple ------------------------------------
def test_every_filing_option_forwards_its_exact_accession():
    options = load_filing_options()
    assert len(options) == 18
    assert len({o.ticker for o in options}) == 10
    for o in options:
        req, err = resolve_request(o.label, o.filing_period_end, "consolidated")
        assert err == "" and req.accession == o.accession and req.filing_period_end == o.filing_period_end


def test_apple_2023_selection_forwards_2023_accession_not_2021():
    req = request_for("AAPL", 2023)
    assert req.accession == "0000320193-23-000106"
    # A 2021 value period is a legitimate comparative of the 2023 filing, but the filing stays 2023.
    comparative, err = resolve_request(option("AAPL", 2023).label, "2021-09-25", "consolidated")
    assert err == "" and comparative.accession == "0000320193-23-000106"
    assert comparative.value_period_end == "2021-09-25"


@pytest.mark.parametrize("label,period,scope", [
    ("Apple Inc. (AAPL) — 2099 10-K", "2021-09-25", "consolidated"),   # unsupported selection
    (None, "2021-09-25", "consolidated"),
    ("__AAPL21__", "not-a-date", "consolidated"),                      # malformed period
    ("__AAPL21__", "2018-09-29", "consolidated"),                      # not reported by the filing
    ("__AAPL21__", "2021-09-25", "segment"),                           # unsupported scope
])
def test_resolve_request_rejects_unsupported_inputs(label, period, scope):
    label = option("AAPL", 2021).label if label == "__AAPL21__" else label
    req, err = resolve_request(label, period, scope)
    assert req is None and err


# ---- F27: arithmetic is licensed only by request-matching included evidence -----------------
def test_matching_request_and_included_records_succeed(app):
    res = app.answer_interactive("Apple gross margin FY2021?", request=request_for("AAPL", 2021),
                                 calculation_plan=PLAN, included_records=make_demo_records())
    assert res["status"] == "ok" and "41.78" in res["answer"]
    assert res["evidence_origin"] == "caller_supplied"
    assert res["request"]["accession"] == "0000320193-21-000105"


def test_microsoft_2022_request_refuses_apple_plan_and_evidence(app):
    res = app.answer_interactive("Microsoft segment margin 2022?", request=request_for("MSFT", 2022),
                                 calculation_plan=PLAN, included_records=make_demo_records())
    assert res["status"] == "insufficient_evidence"
    assert res["answer"] == "" and res["calculations"] == [] and res["evidence"] == []
    assert "does not match requested company" in res["message"]


def test_wrong_filing_refuses_even_when_issuer_matches(app):
    res = app.answer_interactive("Apple FY2021 margin from the 2023 filing?", request=request_for("AAPL", 2023, "2021-09-25"),
                                 calculation_plan=PLAN, included_records=make_demo_records())
    assert res["status"] == "insufficient_evidence" and "comes from filing" in res["message"]


def test_wrong_value_period_refuses(app):
    # Plan/evidence are FY2021 but the request asks for the prior comparative period.
    res = app.answer_interactive("Apple FY2020 margin?", request=request_for("AAPL", 2021, "2020-09-26"),
                                 calculation_plan=PLAN, included_records=make_demo_records())
    assert res["status"] == "insufficient_evidence" and "requested value period" in res["message"]


def test_wrong_scope_evidence_refuses(app):
    records = copy.deepcopy(make_demo_records())
    records[0]["metadata"]["scope"] = "segment"
    res = app.answer_interactive("Apple margin?", request=request_for("AAPL", 2021),
                                 calculation_plan=PLAN, included_records=records)
    assert res["status"] == "insufficient_evidence" and "scope" in res["message"]


def test_empty_evidence_refuses(app):
    res = app.answer_interactive("Apple margin?", request=request_for("AAPL", 2021),
                                 calculation_plan=PLAN, included_records=[])
    assert res["status"] == "insufficient_evidence" and "No accepted evidence" in res["message"]


def test_excluded_operand_refuses(app):
    records = make_demo_records()[:1]  # 'cost' was excluded by the context budget
    res = app.answer_interactive("Apple margin?", request=request_for("AAPL", 2021),
                                 calculation_plan=PLAN, included_records=records)
    assert res["status"] == "insufficient_evidence" and "not in included context" in res["message"]


def test_default_facts_never_produce_a_verified_answer(app):
    # No engine, no records: previously returned status ok with Apple 2021 default facts.
    res = app.answer_interactive("Microsoft 2022 segment margin?", request=request_for("MSFT", 2022),
                                 calculation_plan=PLAN)
    assert res["status"] == "index_not_ready" and res["answer"] == ""
    loose = app.answer_interactive("Apple margin?", calculation_plan=PLAN)
    assert loose["status"] == "invalid_request" and loose["answer"] == ""


def test_demo_only_is_a_distinct_never_ok_status(app):
    res = app.answer_interactive("Apple margin?", request=request_for("AAPL", 2021),
                                 calculation_plan=PLAN, demo_only=True)
    assert res["status"] == "demo_only" and res["status"] != "ok"
    assert res["answer"].startswith("[DEMO ONLY") and res["evidence_origin"] == "synthetic_demo"
    # Even the demo cannot answer another issuer's request.
    other = app.answer_interactive("Microsoft margin?", request=request_for("MSFT", 2022),
                                   calculation_plan=PLAN, demo_only=True)
    assert other["status"] == "insufficient_evidence" and other["answer"] == ""


# ---- engine branch: canonical filters + post-retrieval request binding -----------------------
class FakeEngine:
    def __init__(self, evidence, status="ok", raises=False):
        self.evidence, self.status, self.raises, self.calls = evidence, status, raises, []

    def answer_financial_question(self, question, calculation_plan=None, filters=None):
        self.calls.append(filters)
        if self.raises:
            raise RuntimeError("provider down")
        return {"status": self.status, "answer": "Verified.", "message": "", "evidence": self.evidence,
                "calculations": [{"status": "ok"}], "retrieval_trace": {"routing": "fake"}}


def test_engine_receives_canonical_ticker_accession_filters_and_validated_evidence(app):
    engine = FakeEngine(make_demo_records())
    app.engine = engine
    res = app.answer_interactive("Apple margin?", request=request_for("AAPL", 2021), calculation_plan=PLAN)
    assert res["status"] == "ok" and res["evidence_origin"] == "engine_retrieved"
    assert engine.calls == [{"ticker": "AAPL", "accession": "0000320193-21-000105"}]


def test_engine_evidence_from_other_filing_is_refused_and_cleared(app):
    app.engine = FakeEngine(make_demo_records())
    res = app.answer_interactive("Apple margin 2023?", request=request_for("AAPL", 2023, "2021-09-25"),
                                 calculation_plan=PLAN)
    assert res["status"] == "insufficient_evidence" and res["answer"] == ""
    assert res["evidence"] == [] and res["calculations"] == []


def test_engine_empty_evidence_and_failure_are_refused(app):
    app.engine = FakeEngine([])
    assert app.answer_interactive("q", request=request_for("AAPL", 2021))["status"] == "insufficient_evidence"
    app.engine = FakeEngine([], raises=True)
    res = app.answer_interactive("q", request=request_for("AAPL", 2021))
    assert res["status"] == "service_error" and res["answer"] == ""
    app.engine = FakeEngine(make_demo_records())
    assert app.answer_interactive("q")["status"] == "invalid_request"  # no validated request


def test_two_independent_requests_do_not_share_results(app):
    first = app.answer_interactive("Apple margin?", request=request_for("AAPL", 2021),
                                   calculation_plan=PLAN, included_records=make_demo_records())
    second = app.answer_interactive("Microsoft margin?", request=request_for("MSFT", 2022),
                                    calculation_plan=PLAN, included_records=make_demo_records())
    assert first["status"] == "ok" and second["status"] == "insufficient_evidence"
    assert second["answer"] == "" and second["request"]["ticker"] == "MSFT"
    assert first["request"]["ticker"] == "AAPL"


# ---- F24: operand helper shares the evaluator's strictness ------------------------------------
@pytest.mark.parametrize("expression", [
    {"op": "subtract", "args": [{"evidence_id": "sales"}, {"bogus": 1}]},          # unknown child
    {"op": "subtract", "args": [{"evidence_id": "sales"}, {"evidence_id": "cost"}, {"evidence_id": "x"}]},
    {"op": "eval", "args": [{"evidence_id": "sales"}, {"evidence_id": "cost"}]},    # forbidden op
    {"op": "subtract", "args": [{"evidence_id": "sales"}, "cost"]},                  # non-object child
    {"evidence_id": ""},
])
def test_helper_rejects_malformed_expressions(expression):
    ok, message = verify_included_operands({**PLAN, "expression": expression}, ["sales", "cost", "x"])
    assert ok is False and message


def test_helper_rejects_overdeep_and_accepts_canonical():
    node = {"evidence_id": "sales"}
    for _ in range(9):
        node = {"op": "add", "args": [node, {"evidence_id": "cost"}]}
    assert verify_included_operands({**PLAN, "expression": node}, ["sales", "cost"])[0] is False
    assert verify_included_operands(PLAN, ["sales", "cost"]) == (True, "")
