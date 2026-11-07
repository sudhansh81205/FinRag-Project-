"""Build exact BGE/FAISS only after the merged source/restore gate passes."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.contracts import sha256, strict_json  # noqa: E402
from src.evidence_audit import audit_package, candidate_sidecars  # noqa: E402
from src.indexing.bge import BGEEncoder  # noqa: E402
from src.indexing.store import checked, publish_filing  # noqa: E402


def accepted_input(package, report_path):
    audit = audit_package(package, ROOT)
    checked(audit["status"] == "passed", "Independent source predicates failed")
    report = strict_json(report_path.read_text(encoding="utf-8"))
    checked(report.get("task_gate") == "passed", "Source/restore/tracking gate has not passed")
    for name in ("source_audit", "sidecars", "real_package_restore", "tracking"):
        checked(report.get(name, {}).get("status") == "passed", f"Missing passed {name}")
    for key in (
        "files_sha256",
        "record_schema_sha256",
        "ordered_candidate_ids_sha256",
        "source_sha256",
        "pdf_sha256",
    ):
        checked(
            report["source_audit"].get(key) == audit[key], "Stale audit report; rerun validation"
        )
    checked(
        set(report.get("code_sha256", {}))
        == {
            "src/evidence_audit.py",
            "scripts/verify_canonical_data.py",
            "scripts/prepare_evidence.py",
        },
        "Missing audit code fingerprints",
    )
    for name, digest in report["code_sha256"].items():
        checked((ROOT / name).resolve().is_relative_to(ROOT), "Audit code path escapes repository")
        checked(
            sha256((ROOT / name).read_bytes()) == digest, "Audit code changed; rerun validation"
        )
    for name, payload in candidate_sidecars(package).items():
        checked(report["sidecar_sha256"].get(name) == sha256(payload), "Audited sidecar mismatch")
    data = strict_json((package / "evidence.json").read_text(encoding="utf-8"))
    provenance = {
        "profile": audit["profile"],
        "source_sha256": audit["source_sha256"],
        "pdf_sha256": audit["pdf_sha256"],
        "files_sha256": audit["files_sha256"],
        "ordered_candidate_ids_sha256": audit["ordered_candidate_ids_sha256"],
        "record_schema_sha256": audit["record_schema_sha256"],
        "audit_code_sha256": report["code_sha256"],
        "source_restore_gate": "passed",
    }
    return data["narratives"] + data["cells"], data["parent_tables"], provenance


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, default=ROOT / "data/processed/nov04")
    parser.add_argument("--audit", type=Path, default=ROOT / "output/shanay/canonical_audit.json")
    parser.add_argument("--store", type=Path, default=ROOT / "data/index/bge-faiss")
    parser.add_argument("--model-cache", type=Path, default=ROOT / "output/models")
    parser.add_argument(
        "--download-model", action="store_true", help="Allow the pinned public model download"
    )
    args = parser.parse_args(argv)
    try:
        records, parents, provenance = accepted_input(args.package, args.audit)
        encoder = BGEEncoder(
            cache_folder=str(args.model_cache), local_files_only=not args.download_model
        )
        vectors = encoder.encode([r["content"] for r in records])
        result = publish_filing(
            args.store, records, parents, vectors, provenance, spec=encoder.spec
        )
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, f"Index build failed: {type(exc).__name__}: {exc}\n")


if __name__ == "__main__":
    main()
