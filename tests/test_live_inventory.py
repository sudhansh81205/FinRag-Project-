"""Actual inputs, changed bytes and draft freeze must not create acceptance claims."""
import json

import pytest

from scripts.freeze_controls_manifest import prepare_draft
from src.benchmark.inventory import FILES, build_inventory, digest


def fixtures(tmp_path):
    for name, filename in FILES.items():
        rows = [{"case_id": name + "-1", "benchmark": name, "question": "What happened?",
                 "context_text": ["Original context"], "gold": {"gold_answer": "reference"}}]
        (tmp_path / filename).write_text(json.dumps(rows))


def test_inventory_binds_actual_cases_and_changed_import_manifest(tmp_path):
    fixtures(tmp_path)
    from src.benchmark.runner import ROOT
    inventory = build_inventory(tmp_path, ROOT / "data/charts")
    assert inventory["total_selected_cases"] == 53
    assert inventory["primary_variant_queries"] == 371
    assert inventory["benchmarks"]["FinQA"]["scope"] == "selected_file_only"
    imported = {"files_sha256": {f: digest(tmp_path / f) for f in FILES.values()},
                "counts": dict.fromkeys(FILES.values(), 1), "subsets": False}
    (tmp_path / "import_manifest.json").write_text(json.dumps(imported))
    declared = build_inventory(tmp_path, ROOT / "data/charts")
    assert declared["benchmarks"]["FinQA"]["scope"] == "selected_file_only"
    (tmp_path / FILES["FinQA"]).write_text((tmp_path / FILES["FinQA"]).read_text() + "\n")
    with pytest.raises(ValueError, match="differs"):
        build_inventory(tmp_path, ROOT / "data/charts")


def test_freeze_script_prepares_draft_without_named_review_or_capacity(tmp_path):
    fixtures(tmp_path)
    draft = prepare_draft(tmp_path)
    assert draft["status"] == "draft_not_frozen"
    assert draft["frozen_by"] is None and draft["frozen_at"] is None
    assert draft["capacity_gate_decision"]["estimated_hours"] is None
    assert draft["execution_parameters"]["context_token_budget"] is None
    assert not draft["final_experiment_ready"]
