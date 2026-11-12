"""Approval fixtures test the gate; they are not real human approvals or gold."""

import copy
import json
from pathlib import Path

import pytest

from scripts.promote_chart_set import main
from src.charts.dataset import case_fingerprint, load_candidate_set, load_reviewed_set, sha

CHARTS = Path(__file__).resolve().parents[1] / "data/charts"


@pytest.fixture
def approval(tmp_path):
    cases, _, audit = load_candidate_set(CHARTS)
    ledger = {
        "schema_version": 1,
        "candidate_binding": {
            "question_set_sha256": sha((CHARTS / "question-set.json").read_bytes()),
            "question_files_sha256": audit["question_files_sha256"],
            "source_manifest_sha256": audit["source_manifest_sha256"],
        },
        "reviewer_identity": "independent-fixture-reviewer",
        "reviewed_at": "2026-01-01T00:00:00+00:00",
        "method": "human_original_image_and_source",
        "decisions": [{"id": case["id"], "case_sha256": case_fingerprint(case),
                       "decision": "passed", "original_image_checked": True,
                       "source_provenance_checked": True, "basis": "Synthetic approval fixture only"}
                      for case in cases],
    }
    path = tmp_path / "approval.json"
    return path, ledger


def load_fixture(path, ledger):
    path.write_text(json.dumps(ledger), encoding="utf-8")
    return load_reviewed_set(CHARTS, path,
        trusted_reviewers={"independent-fixture-reviewer"}, label_authors={"fixture-author"})


def test_reviewed_copy_preserves_labels_splits_and_candidate_files(approval):
    path, ledger = approval
    before, _, _ = load_candidate_set(CHARTS)
    reviewed, _, audit = load_fixture(path, ledger)
    assert audit["evaluation_ready"] and not audit["chart_descriptions_approved"]
    assert audit["counts"] == {"dev": 15, "heldout": 35}
    assert [q["id"] for q in before] == [q["id"] for q in reviewed]
    for candidate, promoted in zip(before, reviewed, strict=True):
        assert candidate["answer"] == promoted["answer"]
        assert candidate["split"] == promoted["split"]
        assert candidate["image_sha256"] == promoted["image_sha256"]
        assert promoted["independent_review"] == "passed"
    assert all(case["independent_review"] == "pending" for case in load_candidate_set(CHARTS)[0])


@pytest.mark.parametrize("defect", ["self_review", "unknown_reviewer", "missing", "duplicate",
    "stale_case", "stale_file", "failed", "no_image", "no_source", "no_basis", "no_zone", "future"])
def test_missing_ambiguous_or_self_authored_approvals_block(approval, defect):
    path, ledger = approval
    decision = ledger["decisions"][0]
    if defect == "self_review":
        ledger["reviewer_identity"] = "fixture-author"
    elif defect == "unknown_reviewer":
        ledger["reviewer_identity"] = "untrusted"
    elif defect == "missing":
        ledger["decisions"].pop()
    elif defect == "duplicate":
        ledger["decisions"][1] = copy.deepcopy(decision)
    elif defect == "stale_case":
        decision["case_sha256"] = "0" * 64
    elif defect == "stale_file":
        ledger["candidate_binding"]["question_set_sha256"] = "0" * 64
    elif defect == "failed":
        decision["decision"] = "failed"
    elif defect == "no_image":
        decision["original_image_checked"] = False
    elif defect == "no_source":
        decision["source_provenance_checked"] = False
    elif defect == "no_basis":
        decision["basis"] = ""
    elif defect == "no_zone":
        ledger["reviewed_at"] = "2026-01-01T00:00:00"
    elif defect == "future":
        ledger["reviewed_at"] = "2999-01-01T00:00:00+00:00"
    with pytest.raises(ValueError):
        load_fixture(path, ledger)


def test_duplicate_json_keys_are_not_an_approval(approval):
    path, ledger = approval
    raw = json.dumps(ledger).replace('"schema_version": 1', '"schema_version": 0, "schema_version": 1')
    path.write_text(raw, encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate JSON"):
        load_reviewed_set(CHARTS, path, trusted_reviewers={"independent-fixture-reviewer"},
                          label_authors={"fixture-author"})


def test_cli_saves_explicit_blocked_gate_without_fabricating_approvals(tmp_path):
    output = tmp_path / "gate.json"
    code = main(["--charts", str(CHARTS), "--approvals", str(tmp_path / "absent.json"),
                 "--trusted-reviewer", "independent-fixture-reviewer", "--label-author", "fixture-author",
                 "--output", str(output)])
    gate = json.loads(output.read_bytes())
    assert code == 1 and gate["status"] == "blocked" and not gate["evaluation_ready"]
    assert gate["candidate_files_modified"] is False


def test_cli_writes_hash_bound_fixture_gate(approval, tmp_path):
    path, ledger = approval
    path.write_text(json.dumps(ledger), encoding="utf-8")
    output = tmp_path / "gate.json"
    assert main(["--charts", str(CHARTS), "--approvals", str(path),
                 "--trusted-reviewer", "independent-fixture-reviewer", "--label-author", "fixture-author",
                 "--output", str(output)]) == 0
    gate = json.loads(output.read_bytes())
    assert gate["evaluation_ready"] and len(gate["case_ids"]) == 50
    assert gate["label_authors"] == ["fixture-author"]
    assert gate["candidate_files_modified"] is False


def test_cli_does_not_claim_an_unwritable_gate_saved(tmp_path, capsys):
    blocked = tmp_path / "file"
    blocked.write_text("not a directory", encoding="utf-8")
    assert main(["--charts", str(CHARTS), "--approvals", str(tmp_path / "absent.json"),
                 "--trusted-reviewer", "independent-fixture-reviewer", "--label-author", "fixture-author",
                 "--output", str(blocked / "gate.json")]) == 1
    diagnostic = json.loads(capsys.readouterr().out)
    assert diagnostic["output"] is None and diagnostic["reason"] == "report_destination_unwritable"
