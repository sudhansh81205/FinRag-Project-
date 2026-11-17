"""R3/R5/R6/R7/R8/R12/R13: positive/negative evidence for F23/F27/F29/F35/F36.

Common A-G controls; KR typed period/currency premises and reproducible output identity.
Viva: why do a correct number and matching file bytes not prove a valid financial answer?
"""
import importlib.util
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from src.application import (
    InteractiveApplication,
    load_filing_options,
    make_demo_records,
    resolve_request,
)
from src.benchmark.loaders import GoldReference
from src.benchmark.metrics import evaluate_numerical_match
from src.config import load_settings
from tests.test_nov16_runner_capacity_gates import engine_for, make_runner


@pytest.mark.parametrize("field,value", [("is_ready", True), ("missing_gates", []), ("status", "ready"),
                                        ("variant", "G"), ("frozen_controls", {})])
def test_redundant_manifest_fields_cannot_bypass_current_readiness(tmp_path, field, value):
    runner = make_runner(tmp_path, gates=set())
    runner.init_or_validate_manifest()
    saved = json.loads(runner.manifest_path.read_text())
    saved[field] = value
    runner.manifest_path.write_text(json.dumps(saved))
    with pytest.raises(RuntimeError, match="Resumption rejected"):
        make_runner(tmp_path, gates=set()).run()


@pytest.mark.parametrize("change", ["run_id", "variant", "input_sha256", "answer", "duplicate", "malformed"])
def test_saved_outputs_must_belong_to_unique_unchanged_run_case(tmp_path, change):
    runner = make_runner(tmp_path)
    runner.run(max_cases=1)
    row = json.loads(runner.results_path.read_text())
    if change == "duplicate":
        text = json.dumps(row) + "\n" + json.dumps(row) + "\n"
    elif change == "malformed":
        text = '{"case_id":'
    else:
        row[change] = "foreign"
        text = json.dumps(row) + "\n"
    runner.results_path.write_text(text)
    engine = engine_for("C")
    with pytest.raises(RuntimeError, match="ledger row"):
        make_runner(tmp_path, engine=engine).run()
    assert engine.answer_financial_question.call_count == 0


def test_unchanged_checkpoint_resumes_only_missing_cases(tmp_path):
    make_runner(tmp_path).run(max_cases=1)
    engine = engine_for("C")
    summary = make_runner(tmp_path, engine=engine).run()
    assert summary["status"] == "completed" and summary["attempted_outputs"] == 3
    assert engine.answer_financial_question.call_count == 2


@pytest.mark.parametrize("period,status", [("2020-09-26", "insufficient_evidence"), ("2021-09-25", "ok")])
def test_engine_without_supplied_plan_must_match_selected_value_period(period, status):
    option = next(o for o in load_filing_options() if o.ticker == "AAPL" and o.filing_period_end.startswith("2021"))
    request, _ = resolve_request(option.label, period, "consolidated")
    engine = Mock()
    engine.answer_financial_question.return_value = {
        "status": "ok", "answer": "FY2021 margin 41.78%", "evidence": make_demo_records(),
        "retrieval_trace": {}, "calculations": []}
    app = InteractiveApplication(load_settings(environ={}), engine)
    result = app.answer_interactive("What was the margin?", request=request)
    assert result["status"] == status
    if status != "ok":
        assert result["answer"] == "" and result["calculations"] == []


@pytest.mark.parametrize("prediction,correct", [("0.1 billion USD", True), ("100 million USD", True),
    ("100 million EUR", False), ("100 million JPY", False), ("€100 million", False),
    ("100 billion USD", False), ("100 million USD and 100 million EUR", False)])
def test_explicit_currency_and_scale_must_be_comparable(prediction, correct):
    gold = GoldReference("g", "test", "100 million USD", 100)
    assert evaluate_numerical_match(prediction, gold) is correct


def test_percentage_points_and_explicit_period_are_not_interchangeable():
    gold = GoldReference("g", "test", "20%", 20, period_end="2021-09-25")
    assert evaluate_numerical_match("FY2021: 20%", gold)
    assert not evaluate_numerical_match("FY2020: 20%", gold)
    assert not evaluate_numerical_match("20 percentage points", gold)


def verifier():
    path = Path(__file__).resolve().parents[1] / "scripts/verify_release_package.py"
    spec = importlib.util.spec_from_file_location("release_verifier", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("payload", [{}, {"file_hashes": {}}, {"file_hashes": {"present": "a"*64}, "file_count": 16}])
def test_empty_and_incomplete_release_manifest_refuse(tmp_path, payload):
    module = verifier()
    module.ROOT = tmp_path
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(payload))
    assert not module.verify_manifest(path)[0]


def test_complete_release_manifest_and_file_tamper(tmp_path):
    module = verifier()
    module.ROOT = tmp_path
    for name in set(module.CORE_SOURCE_FILES + module.CRITICAL_RELEASE_FILES):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"fixture")
    hashes = module.generate_manifest()
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"file_hashes": hashes, "file_count": len(hashes)}))
    assert module.verify_manifest(manifest) == (True, [])
    (tmp_path / "app.py").write_bytes(b"tampered")
    assert not module.verify_manifest(manifest)[0]


def test_submission_record_does_not_assert_an_unobserved_upload():
    root = Path(__file__).resolve().parents[1]
    receipt = json.loads((root / "docs/reports/2026-11-17_submission_acknowledgement.json").read_text())
    assert receipt["sign_off"]["status"] == "PREPARED_NOT_SUBMITTED"
    assert receipt["sign_off"]["timestamp"] is None


def test_currency_cannot_be_relabelled_as_shares_or_percentage_points():
    assert not evaluate_numerical_match("100 million shares", GoldReference("g", "test", "100 million USD", 100))
    assert not evaluate_numerical_match("€20 percentage points", GoldReference("g", "test", "20 percentage points", 20))
