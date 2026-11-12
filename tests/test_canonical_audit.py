"""Real-source acceptance and adversarial semantic checks, separate from gold labels."""

import copy
import json
import shutil
from decimal import Decimal
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from scripts import verify_canonical_data as command
from scripts.prepare_evidence import prepare, validate_records
from src.contracts import sha256
from src.evidence_audit import (
    AuditError,
    amount,
    audit_cell,
    audit_package,
    audit_pdf_spans,
    candidate_sidecars,
    verify_sidecars,
)
from src.ingestion.filing_parser import ParseError

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def audited(tmp_path_factory):
    directory = tmp_path_factory.mktemp("canonical-audit")
    prepare(directory)
    package = json.loads((directory / "evidence.json").read_bytes())
    soup = BeautifulSoup((directory / "source.html").read_text(encoding="utf-8"), "lxml")
    parents = {r["evidence_id"]: r for r in package["parent_tables"]}
    ids = {n["id"]: n for n in soup.find_all(id=True)}
    return directory, package, soup, parents, ids


def test_real_source_package_acceptance(audited):
    directory, package, soup, parents, ids = audited
    result = audit_package(directory, ROOT)
    assert result["status"] == "passed", result["failures"]
    assert result["record_count"] == 538 and result["candidate_count"] == 535
    # Opening balances belong to the prior instant despite the current flow
    # column's heading; label facts and hidden tags are not extra value cells.
    opening = [
        r for r in package["cells"] if r["metadata"]["row_label"].endswith("beginning balances")
    ]
    assert len(opening) == 3
    assert opening[0]["metadata"]["period_end"] == "2020-09-26"
    for record in opening:
        audit_cell(record, parents, soup, ids)
    assert amount("—", 6) is None and amount("(85,971)", 6) == -85971000000
    assert amount("5.61", 0) == Decimal("5.61")


@pytest.mark.parametrize(
    ("key", "value", "reason"),
    [
        ("parent_table_id", "unrelated", "missing_parent"),
        ("row_index", 0, "cell_row"),
        ("column_index", 999, "cell_column"),
        ("period_end", "2020-09-26", "cell_period_end"),
        ("period_start", "2021-01-01", "cell_period_start"),
        ("normalized_unit", "shares", "cell_normalized_unit"),
        ("scale", 1, "cell_scale"),
        ("normalized_value", 0, "normalized_amount"),
        ("normalized_value_decimal", "0", "normalized_amount"),
        ("scope", "segment", "cell_scope"),
        ("raw_value", "0", "cell_raw_value"),
        ("metric", "us-gaap:Wrong", "cell_metric"),
        ("footnote_links", ["#invented"], "cell_footnote_links"),
    ],
)
def test_schema_valid_semantic_corruption_rejected(audited, key, value, reason):
    _, package, soup, parents, ids = audited
    record = copy.deepcopy(package["cells"][0])
    record["metadata"][key] = value
    # Reproduce the review gap: the merged builder's shape/hash check accepts
    # these mutations. Source-based predicates must reject them.
    schema = json.loads((ROOT / "data/contracts/canonical_record.schema.json").read_bytes())
    validate_records([record], schema)
    with pytest.raises(AuditError, match=reason):
        audit_cell(record, parents, soup, ids)


def test_ordered_sidecars_reject_swapped_rows(audited, tmp_path):
    directory, *_ = audited
    for name, payload in candidate_sidecars(directory).items():
        (tmp_path / name).write_bytes(payload)
    assert verify_sidecars(directory, tmp_path)["status"] == "passed"
    path = tmp_path / "candidate_metadata.json"
    rows = json.loads(path.read_bytes())
    rows[0], rows[1] = rows[1], rows[0]
    path.write_text(json.dumps(rows), encoding="utf-8")
    with pytest.raises(AuditError, match="sidecar_mismatch"):
        verify_sidecars(directory, tmp_path)


def test_independent_display_fixtures(audited):
    _, package, *_ = audited
    fixtures = json.loads((ROOT / "tests/fixtures/apple2021_audit_cases.json").read_bytes())
    for case in fixtures["cases"]:
        matches = [
            r["metadata"]
            for r in package["cells"]
            if all(
                (
                    r["metadata"]["table_title"] == case["table"],
                    r["metadata"]["row_label"] == case["row"],
                    r["metadata"]["period_end"] == case["period_end"],
                    r["metadata"]["unit"] == case["unit"],
                )
            )
        ]
        assert len(matches) == 1
        assert Decimal(matches[0]["normalized_value_decimal"]) == Decimal(case["value"])


@pytest.mark.parametrize("defect", ["empty", "source_hash", "outside_path", "duplicate"])
def test_bad_package_reject_ledger(audited, tmp_path, defect):
    directory, *_ = audited
    shutil.copytree(directory, tmp_path / "package")
    destination = tmp_path / "package"
    if defect == "source_hash":
        (destination / "source.html").write_text("corrupt", encoding="utf-8")
    else:
        path = destination / "evidence.json"
        data = json.loads(path.read_bytes())
        if defect == "empty":
            data["cells"] = []
        elif defect == "duplicate":
            data["cells"][1] = data["cells"][0]
        path.write_text(json.dumps(data), encoding="utf-8")
        manifest_path = destination / "manifest.json"
        manifest = json.loads(manifest_path.read_bytes())
        manifest["files_sha256"]["evidence.json"] = sha256(path.read_bytes())
        if defect == "outside_path":
            manifest["files_sha256"]["../outside"] = "0" * 64
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    result = audit_package(destination, ROOT)
    assert result["status"] == "failed" and result["failures"]


def test_missing_package_and_tools_save_reports(audited, tmp_path, monkeypatch):
    output = tmp_path / "missing.json"
    assert (
        command.main(
            [
                "--package",
                str(tmp_path / "absent"),
                "--output",
                str(output),
                "--artifacts-dir",
                str(tmp_path / "runs"),
            ]
        )
        == 1
    )
    report = json.loads(output.read_bytes())
    assert report["source_audit"]["status"] == "blocked"
    assert report["real_package_restore"]["status"] == "blocked"
    monkeypatch.setattr(command, "package_info", lambda *args: {"available": False})
    assert command.restore_package(None, None, tmp_path / "unused", None)["status"] == "blocked"
    assert command.track_audit({}, tmp_path / "unused")["status"] == "blocked"
    assert not (tmp_path / "unused").exists()
    directory, *_ = audited
    assert (
        command.main(
            [
                "--package",
                str(directory),
                "--output",
                str(output),
                "--artifacts-dir",
                str(tmp_path / "runs"),
            ]
        )
        == 1
    )
    report = json.loads(output.read_bytes())
    assert report["source_audit"]["status"] == "passed"
    assert report["real_package_restore"] == {"status": "blocked", "reason": "dvc_not_installed"}
    assert report["task_gate"] == "blocked_or_failed"


def test_storage_reingest_preserves_existing_packages(audited, tmp_path):
    directory, *_ = audited
    before = command.tree_hashes(directory)
    prepare(directory)
    assert before == command.tree_hashes(directory)
    foreign = tmp_path / "other-filing"
    foreign.mkdir()
    (foreign / "evidence.json").write_text('{"accession":"another-filing"}', encoding="utf-8")
    original = command.tree_hashes(foreign)
    with pytest.raises(ParseError, match="fresh output directory"):
        prepare(foreign)
    assert original == command.tree_hashes(foreign)
    assert before == command.tree_hashes(directory)


def test_pdf_positions_bind_an_independent_row_and_year(audited):
    from pypdf import PdfReader

    _, package, *_ = audited
    check = copy.deepcopy(package["pdf_corroboration"][0])
    page = PdfReader(ROOT / "data/source/aapl-2021-rendition.pdf").pages[check["page"] - 1]
    headers = ["September 25, 2021", "September 26, 2020", "September 28, 2019"]
    audit_pdf_spans(check, page, headers)
    # Equivalent top-left coordinates are supported only after conversion.
    top = copy.deepcopy(check)
    for span in top["source_spans"]:
        x0, y0, x1, y1 = span["bbox"]
        span.update(origin="TOPLEFT", bbox=[x0, float(page.mediabox.height) - y1,
                                          x1, float(page.mediabox.height) - y0])
    audit_pdf_spans(top, page, headers)
    wrong = copy.deepcopy(check)
    wrong["source_spans"][0]["bbox"] = [100, 100, 120, 108]
    with pytest.raises(AuditError, match="independent_text_anchor"):
        audit_pdf_spans(wrong, page, headers)
    wrong = copy.deepcopy(check)
    wrong["source_spans"][0]["origin"] = "invented-origin"
    with pytest.raises(AuditError, match="coordinate_origin"):
        audit_pdf_spans(wrong, page, headers)
    wrong = copy.deepcopy(check)
    wrong["column_header"] = "September 26, 2020"
    with pytest.raises(AuditError, match="year_column"):
        audit_pdf_spans(wrong, page, headers)
    wrong = copy.deepcopy(check)
    wrong["row_label"] = "Total assets"
    with pytest.raises(AuditError, match="independent_row"):
        audit_pdf_spans(wrong, page, headers)


def test_artifact_startup_failure_still_saves_diagnostic(tmp_path, monkeypatch):
    blocked = tmp_path / "existing-file"
    blocked.write_text("not a directory", encoding="utf-8")
    output = tmp_path / "writable" / "report.json"
    monkeypatch.setattr(command, "build_report", lambda *_: pytest.fail("Startup guard should stop here"))
    assert command.main(["--artifacts-dir", str(blocked), "--output", str(output)]) == 1
    report = json.loads(output.read_bytes())
    assert report["status"] == "failed" and report["exception_type"] == "FileExistsError"
    assert blocked.read_text(encoding="utf-8") == "not a directory"


def test_unwritable_report_destination_is_not_claimed_saved(tmp_path, capsys):
    blocked = tmp_path / "existing-file"
    blocked.write_text("not a directory", encoding="utf-8")
    assert command.main(["--package", str(tmp_path / "absent"), "--artifacts-dir", str(tmp_path / "runs"),
                         "--output", str(blocked / "report.json")]) == 1
    diagnostic = json.loads(capsys.readouterr().out)
    assert diagnostic["report"] is None and diagnostic["diagnostic_write_error"]
