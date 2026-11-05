"""F9/F10 adversarial fixtures. Synthetic checks do not certify source truth."""

import copy
import gzip
import json
import shutil
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from scripts import verify_day05_environment as environment
from src.contracts import canonical_record, sha256, verify_parser_package

ROOT = Path(__file__).resolve().parents[1]


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


@pytest.fixture
def package(tmp_path):
    source = b"synthetic source, not financial evidence"
    archive = gzip.compress(source)
    (tmp_path / "data/source").mkdir(parents=True)
    (tmp_path / "data/source/test.gz").write_bytes(archive)
    (tmp_path / "data/contracts").mkdir()
    shutil.copyfile(ROOT / "data/contracts/canonical_record.schema.json", tmp_path / "data/contracts/canonical_record.schema.json")
    manifest = {"accession": "fixture", "ticker": "TEST", "raw_sha256": sha256(source),
                "source_url": "https://example.com/fixture", "raw_path": "data/raw/test.html",
                "source_archive": "data/source/test.gz", "source_archive_sha256": sha256(archive), "parsed_record_count": 2}
    write_json(tmp_path / "data/filing_manifest.json", manifest)
    records = []
    for kind in ("narrative_text", "financial_table"):
        content, locator = f"fixture {kind}", f"#{kind}"
        digest = sha256(content.encode())
        identity = f"fixture:item8:{kind}:{sha256(locator.encode())[:12]}:{digest[:16]}"
        meta = {"accession": "fixture", "ticker": "TEST", "section": "Item 8", "source_url": manifest["source_url"],
                "source_locator": locator, "source_sha256": manifest["raw_sha256"], "content_sha256": digest,
                "type": kind, "record_schema_version": 1, "parser_version": "fixture-v1"}
        record = {"id": identity, "content": content, "metadata": meta}
        if kind == "financial_table":
            meta.update(parent_table_id=identity, table_title="fixture", periods_json="[2021]", headers_json='["2021"]', units_json='{"normalization":"not_performed"}')
            record["source_rows"] = [{"source_locator": "#row", "cells": [{"column": 0, "colspan": 1, "text": "1"}]}]
        records.append(record)
    save_package(tmp_path, records[:1], records[1:])
    return tmp_path, records


def save_package(root, narratives, tables):
    output = root / "data/processed/apple-2021"
    output.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for filename, records in (("narrative.jsonl", narratives), ("tables.jsonl", tables)):
        payload = "".join(json.dumps(r) + "\n" for r in records).encode()
        (output / filename).write_bytes(payload)
        hashes[filename] = sha256(payload)
    manifest = json.loads((root / "data/filing_manifest.json").read_text())
    manifest["parsed_record_count"] = len(narratives) + len(tables)
    write_json(root / "data/filing_manifest.json", manifest)
    write_json(output / "parsing_summary.json", {"source_sha256": manifest["raw_sha256"], "accession": "fixture",
        "parser_version": "fixture-v1", "output_sha256": hashes, "total_records": len(narratives) + len(tables),
        "narrative_records": len(narratives), "table_records": len(tables)})


def test_valid_package_and_lossless_canonical_adapter(package):
    root, records = package
    original = copy.deepcopy(records[1])
    assert verify_parser_package(root)["status"] == "passed"
    adapted = canonical_record(original)
    assert adapted["evidence_id"] == original["id"] and "id" not in adapted
    assert adapted["source_rows"] == original["source_rows"]
    assert records[1] == original
    with pytest.raises(ValueError):
        canonical_record({**original, "evidence_id": "different"})


@pytest.mark.parametrize("defect", ["empty", "duplicate", "source_hash", "content_hash", "wrong_accession", "parent", "blank_id", "wrong_id", "malformed", "missing_grid"])
def test_invalid_package_cannot_pass_even_with_updated_file_hashes(package, defect):
    root, records = package
    narratives, tables = records[:1], records[1:]
    if defect == "empty":
        narratives, tables = [], []
    elif defect == "duplicate":
        narratives *= 2
    elif defect in {"source_hash", "content_hash"}:
        narratives[0]["metadata"][defect.replace("_hash", "_sha256")] = "0" * 64
    elif defect == "wrong_accession":
        narratives[0]["metadata"]["accession"] = "wrong"
    elif defect == "parent":
        tables[0]["metadata"]["parent_table_id"] = "wrong"
    elif defect in {"blank_id", "wrong_id"}:
        narratives[0]["id"] = " " if defect == "blank_id" else "wrong"
    elif defect == "malformed":
        narratives = [None]
    elif defect == "missing_grid":
        del tables[0]["source_rows"]
    save_package(root, narratives, tables)
    report = verify_parser_package(root)
    assert report["status"] == "failed"
    assert report["failures"]
    assert not report["full_canonical_package_ready"]


def test_tampering_after_summary_and_missing_source_fail(package):
    root, _ = package
    (root / "data/processed/apple-2021/narrative.jsonl").write_text("{}\n")
    assert verify_parser_package(root)["status"] == "failed"
    (root / "data/source/test.gz").unlink()
    assert verify_parser_package(root)["status"] == "blocked"


@pytest.mark.parametrize("kind", ["table_cell", "chart"])
def test_future_types_need_their_declared_fields(package, kind):
    root, records = package
    record = canonical_record(records[0])
    record["metadata"]["type"] = kind
    schema = json.loads((root / "data/contracts/canonical_record.schema.json").read_text())
    assert list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(record))


def test_missing_tools_still_save_diagnostic_and_fail_exit(tmp_path, monkeypatch):
    monkeypatch.setattr(environment, "ROOT", tmp_path)
    monkeypatch.setattr(environment, "package_info", lambda *a: {"available": False, "version": None})
    monkeypatch.setattr(environment, "run_command", lambda *a, **k: {"status": "blocked", "reason": "executable_not_found"})
    monkeypatch.setattr(environment, "resource_inventory", lambda: {"memory_bytes": None})
    monkeypatch.setattr(environment, "ollama_inventory", lambda: {"status": "unavailable"})
    output = tmp_path / "report.json"
    code = environment.main(["--output", str(output), "--artifacts-dir", str(tmp_path / "runs")])
    report = json.loads(output.read_text())
    assert code == 1
    assert report["parser_contract"]["status"] == "blocked"
    assert report["dvc_restore_smoke"]["status"] == "blocked"
    assert report["mlflow_logging_smoke"]["reason"] == "parser_contract_not_passed"
    assert report["python"]["executable"] == environment.sys.executable


def test_exceptions_are_reported_without_private_values():
    def bad():
        raise RuntimeError("private-token")
    report = environment.guarded(bad)
    assert report == {"status": "failed", "reason": "check_exception", "exception_type": "RuntimeError"}


def test_index_sidecar_requires_pinned_identity_and_preprocessing():
    schema = json.loads((ROOT / "data/contracts/index_sidecar.schema.json").read_text())
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    valid = {"index_format": "faiss.IndexFlatIP", "embedding_model": "BAAI/bge-base-en-v1.5",
             "embedding_revision": "a" * 40, "dimension": 768, "normalization": "l2",
             "evidence_ids_sha256": "0" * 64, "metadata_sidecar_sha256": "1" * 64,
             "index_sha256": "2" * 64, "parent_table_storage": "parents.jsonl", "parent_table_sha256": "3" * 64,
             "record_count": 1, "id_order_encoding": "utf8-json-array-compact-no-ascii-escape",
             "preprocessing": {"query_instruction": "fixture", "document_instruction": "",
                               "max_seq_length": 512, "truncation_policy": "declared-fixture-only"}}
    assert not list(validator.iter_errors(valid))
    for key, wrong in (("dimension", 384), ("embedding_revision", "main"), ("record_count", 0),
                       ("metadata_sidecar_sha256", ""), ("preprocessing", {})):
        assert list(validator.iter_errors({**valid, key: wrong}))
