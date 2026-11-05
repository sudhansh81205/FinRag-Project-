"""Executable boundary for the existing HTML parser, not an independent source audit."""

import copy
import gzip
import hashlib
import json
from pathlib import Path


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_record(record: dict) -> dict:
    """Rename the legacy id without changing identity or dropping the parent grid."""
    if not isinstance(record, dict):
        raise ValueError("Record must be an object.")
    result = copy.deepcopy(record)
    legacy = result.pop("id", None)
    identity = result.get("evidence_id", legacy)
    if legacy is not None and legacy != identity:
        raise ValueError("Conflicting id and evidence_id.")
    if not isinstance(identity, str) or not identity.strip():
        raise ValueError("Missing evidence identity.")
    result["evidence_id"] = identity
    return result


def strict_json(text):
    def invalid_constant(value):
        raise ValueError("Non-finite JSON number.")
    return json.loads(text, parse_constant=invalid_constant)


def within(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Source path escapes the project.")
    return path


def verify_parser_package(root: Path) -> dict:
    """Check existing parser files/schema/hashes; never claim cells/PDF/index readiness."""
    failures, records = [], []
    report = {"status": "failed", "profile": "apple-2021-html-parent-v1",
              "record_count": 0, "failures": failures,
              "independent_source_audit": "pending", "full_canonical_package_ready": False,
              "missing_deliverables": ["typed cells", "PDF fixtures", "chart sources", "expanded corpus"]}
    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ImportError:
        return {**report, "status": "blocked", "reason": "Install requirements-environment.txt (jsonschema)."}
    try:
        manifest = strict_json((root / "data/filing_manifest.json").read_text(encoding="utf-8"))
        output = root / "data/processed/apple-2021"
        summary = strict_json((output / "parsing_summary.json").read_text(encoding="utf-8"))
        schema_path = root / "data/contracts/canonical_record.schema.json"
        schema = strict_json(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        raw_path = within(root, manifest["raw_path"])
        compressed = within(root, manifest["source_archive"]).read_bytes()
        if sha256(compressed) != manifest["source_archive_sha256"]:
            failures.append("source archive hash mismatch")
        raw = raw_path.read_bytes() if raw_path.is_file() else gzip.decompress(compressed)
        if sha256(raw) != manifest["raw_sha256"] or sha256(gzip.decompress(compressed)) != manifest["raw_sha256"]:
            failures.append("raw source hash mismatch")
        if summary["source_sha256"] != manifest["raw_sha256"] or summary["accession"] != manifest["accession"]:
            failures.append("summary/source identity mismatch")
        counts, file_hashes = {}, {}
        for filename, kind, count_key in (
            ("narrative.jsonl", "narrative_text", "narrative_records"),
            ("tables.jsonl", "financial_table", "table_records"),
        ):
            payload = (output / filename).read_bytes()
            file_hashes[filename] = sha256(payload)
            if file_hashes[filename] != summary["output_sha256"][filename]:
                failures.append(f"{filename}: output hash mismatch")
            rows = [strict_json(line) for line in payload.decode("utf-8").splitlines() if line.strip()]
            counts[kind] = len(rows)
            if not rows or len(rows) != summary[count_key]:
                failures.append(f"{filename}: empty or count mismatch")
            for number, row in enumerate(rows, 1):
                label = f"{filename}:{number}"
                try:
                    record = canonical_record(row)
                    errors = list(validator.iter_errors(record))
                    if errors:
                        failures.append(f"{label}: schema failure at {list(errors[0].absolute_path)}")
                        continue
                    meta = record["metadata"]
                    for key, expected in (("accession", manifest["accession"]),
                                          ("ticker", manifest["ticker"]),
                                          ("source_url", manifest["source_url"]),
                                          ("source_sha256", manifest["raw_sha256"]),
                                          ("parser_version", summary["parser_version"]), ("type", kind)):
                        if meta[key] != expected:
                            failures.append(f"{label}: {key} mismatch")
                    digest = sha256(record["content"].encode("utf-8"))
                    location_hash = sha256(meta["source_locator"].encode("utf-8"))[:12]
                    expected_id = (f"{meta['accession']}:{meta['section'].replace(' ', '').lower()}:"
                                   f"{kind}:{location_hash}:{digest[:16]}")
                    if digest != meta["content_sha256"]:
                        failures.append(f"{label}: content hash mismatch")
                    if record["evidence_id"] != expected_id:
                        failures.append(f"{label}: deterministic identity mismatch")
                    if kind == "financial_table" and meta["parent_table_id"] != record["evidence_id"]:
                        failures.append(f"{label}: parent identity mismatch")
                    records.append(record)
                except (KeyError, TypeError, ValueError):
                    failures.append(f"{label}: malformed record")
        identities = [record["evidence_id"] for record in records]
        if len(identities) != len(set(identities)):
            failures.append("duplicate evidence identities")
        total = sum(counts.values())
        if total == 0 or total != summary["total_records"] or total != manifest["parsed_record_count"]:
            failures.append("total record count mismatch or empty package")
        report.update(record_count=total, validated_record_count=len(records), counts=counts,
                      accession=manifest["accession"], source_sha256=sha256(raw),
                      file_sha256=file_hashes, schema_sha256=sha256(schema_path.read_bytes()),
                      record_ids_sha256=sha256("\n".join(sorted(identities)).encode()),
                      status="passed" if not failures else "failed")
    except FileNotFoundError:
        report.update(status="blocked", reason="Missing source/schema/parser outputs; run the existing parser first.")
    except (OSError, EOFError, ValueError, KeyError, TypeError, AttributeError):
        failures.append("malformed or unreadable manifest/summary/source/package")
    return report
