"""Malformed or stale handoffs cannot authorize the production index build."""

import copy
import json

import pytest

from scripts import build_index


@pytest.mark.parametrize("failure", ["restore", "stale", "fingerprints"])
def test_incomplete_handoff_fails_before_embedding(tmp_path, monkeypatch, failure):
    audit = {
        "status": "passed",
        **dict.fromkeys(
            (
                "files_sha256",
                "record_schema_sha256",
                "ordered_candidate_ids_sha256",
                "source_sha256",
                "pdf_sha256",
            ),
            "a" * 64,
        ),
    }
    report = {
        "task_gate": "passed",
        "source_audit": copy.deepcopy(audit),
        "sidecars": {"status": "passed"},
        "real_package_restore": {"status": "passed"},
        "tracking": {"status": "passed"},
        "code_sha256": {},
    }
    if failure == "restore":
        report["real_package_restore"]["status"] = "failed"
    elif failure == "stale":
        report["source_audit"]["source_sha256"] = "b" * 64
    path = tmp_path / "audit.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    monkeypatch.setattr(build_index, "audit_package", lambda *args: audit)
    with pytest.raises(
        ValueError,
        match={"restore": "Missing passed", "stale": "Stale", "fingerprints": "fingerprints"}[
            failure
        ],
    ):
        build_index.accepted_input(tmp_path, path)
