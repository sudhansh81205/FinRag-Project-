"""Shanay's real-package source, sidecar, DVC restore and tracking gate.

Only local disposable copies are removed for the restore. Sources, old indexes,
the submitted package and other filing directories are never modified.
"""

import argparse
import importlib.metadata
import json
import os
import platform
import shutil
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.parse_filing import json_bytes, write_atomic  # noqa: E402
from scripts.verify_day05_environment import guarded, package_info, run_command  # noqa: E402
from src.contracts import sha256  # noqa: E402
from src.evidence_audit import audit_package, candidate_sidecars, verify_sidecars  # noqa: E402


def tree_hashes(directory):
    return {
        p.relative_to(directory).as_posix(): sha256(p.read_bytes())
        for p in sorted(directory.rglob("*"))
        if p.is_file()
    }


def restore_package(package, root, destination, sidecars):
    """Cache and restore the actual audited inputs, not a synthetic fixture."""
    if not package_info("dvc", "dvc")["available"]:
        return {"status": "blocked", "reason": "dvc_not_installed"}
    destination.mkdir(parents=True, exist_ok=False)
    bundle = destination / "bundle"
    shutil.copytree(package, bundle / "evidence")
    shutil.copytree(sidecars, bundle / "sidecars")
    # Include every referenced audit dependency so the restored directory can
    # be checked without reading the original package/repository data.
    for name in (
        "data/filing_manifest.json",
        "data/source/apple-2021-renditions.json",
        "data/source/aapl-2021-rendition.pdf",
        "data/contracts/canonical_record.schema.json",
    ):
        target = bundle / "reference" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / name, target)
    before = tree_hashes(bundle)
    commands = []
    env = {**os.environ, "DVC_NO_ANALYTICS": "1"}
    for arguments in (("init", "--no-scm", "--quiet"), ("add", "bundle", "--quiet")):
        outcome = run_command(
            [sys.executable, "-m", "dvc", *arguments], cwd=destination, timeout=120, env=env
        )
        commands.append({"arguments": list(arguments), **outcome})
        if outcome["status"] != "passed":
            return {"status": "failed", "reason": "dvc_cache_failed", "commands": commands}
    # All files are copies just created in a fresh owned directory. Verify each
    # resolved target remains inside it before unlinking; leave folders intact.
    for relative in before:
        target = (bundle / relative).resolve()
        if not target.is_relative_to(bundle.resolve()):
            raise ValueError("restore target escapes owned bundle")
        target.unlink()
    outcome = run_command(
        [sys.executable, "-m", "dvc", "checkout", "--quiet"], cwd=destination, timeout=120, env=env
    )
    commands.append({"arguments": ["checkout", "--quiet"], **outcome})
    after = tree_hashes(bundle)
    audit = audit_package(bundle / "evidence", bundle / "reference")
    rows = guarded(lambda: verify_sidecars(bundle / "evidence", bundle / "sidecars"))
    passed = (
        outcome["status"] == "passed"
        and before == after
        and audit["status"] == rows["status"] == "passed"
    )
    return {
        "status": "passed" if passed else "failed",
        "scope": "real canonical package and referenced PDF/schema",
        "file_count": len(before),
        "before_sha256": before,
        "after_sha256": after,
        "hashes_equal": before == after,
        "restored_audit": audit,
        "restored_sidecars": rows,
        "commands": commands,
        "artifact_directory": str(destination),
    }


def track_audit(report, directory):
    if not package_info("mlflow", "mlflow")["available"]:
        return {"status": "blocked", "reason": "mlflow_not_installed"}
    from mlflow import MlflowClient

    directory.mkdir(parents=True, exist_ok=False)
    uri = f"sqlite:///{(directory / 'tracking.db').as_posix()}"
    client = MlflowClient(tracking_uri=uri)
    experiment = client.create_experiment(
        "finrag-canonical-audit", artifact_location=(directory / "artifacts").as_uri()
    )
    run = client.create_run(
        experiment, tags={"scope": "source_audit_and_real_restore_not_model_evaluation"}
    )
    identity = run.info.run_id
    for key in ("source_sha256", "record_schema_sha256", "ordered_candidate_ids_sha256"):
        client.log_param(identity, key, report["source_audit"][key])
    client.log_param(identity, "code_revision", report["revision"])
    client.log_metric(identity, "records_audited", report["source_audit"]["record_count"])
    artifact = directory / "canonical_audit.json"
    artifact.write_bytes(json_bytes(report))
    client.log_artifact(identity, str(artifact))
    client.set_terminated(identity)
    reopened = MlflowClient(tracking_uri=uri)
    restored = Path(reopened.download_artifacts(identity, artifact.name))
    readback = reopened.get_run(identity)
    valid = (
        restored.read_bytes() == artifact.read_bytes()
        and readback.info.status == "FINISHED"
        and readback.data.metrics["records_audited"] == report["source_audit"]["record_count"]
    )
    return {
        "status": "passed" if valid else "failed",
        "run_id": identity,
        "readback_verified": valid,
        "artifact_sha256": sha256(restored.read_bytes()),
        "artifact_directory": str(directory),
    }


def build_report(package, artifacts):
    report = {
        "schema_version": 1,
        "owner": "Shanay",
        "scheduled_date": "2026-11-05",
        "requirements": ["R2", "R3", "R13"],
        "variants": "common A-G identity; C parents/cells; G source provenance",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "revision": run_command(["git", "rev-parse", "HEAD"]).get("stdout"),
        "python": platform.python_version(),
        "index_ready": False,
        "code_sha256": {
            name: sha256((ROOT / name).read_bytes())
            for name in (
                "src/evidence_audit.py",
                "scripts/verify_canonical_data.py",
                "scripts/prepare_evidence.py",
            )
        },
        "packages": {d.metadata["Name"]: d.version for d in importlib.metadata.distributions()},
    }
    report["source_audit"] = guarded(lambda: audit_package(package, ROOT))
    audit = report["source_audit"]
    if audit["status"] == "passed":
        sidecars = artifacts / "sidecars"
        sidecars.mkdir()
        for name, payload in candidate_sidecars(package).items():
            write_atomic(sidecars / name, payload)
        report["sidecars"] = guarded(lambda: verify_sidecars(package, sidecars))
        report["sidecar_sha256"] = tree_hashes(sidecars)
        report["real_package_restore"] = guarded(
            lambda: restore_package(package, ROOT, artifacts / "dvc", sidecars)
        )
        if report["real_package_restore"]["status"] == "passed":
            report["tracking"] = guarded(lambda: track_audit(report, artifacts / "mlflow"))
        else:
            report["tracking"] = {"status": "blocked", "reason": "restore_not_passed"}
    else:
        for key in ("sidecars", "real_package_restore", "tracking"):
            report[key] = {"status": "blocked", "reason": "source_audit_not_passed"}
    report["task_gate"] = (
        "passed"
        if all(
            report[k]["status"] == "passed"
            for k in ("source_audit", "sidecars", "real_package_restore", "tracking")
        )
        else "blocked_or_failed"
    )
    report["remaining_scope"] = [
        "BGE/FAISS vector build and row mapping",
        "wider corpus ingestion",
        "arbitrary PDF/OCR layouts",
        "chart captions and independent question labels",
        "full A-G evaluation",
    ]
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, default=ROOT / "data/processed/nov04")
    parser.add_argument("--output", type=Path, default=ROOT / "output/shanay/canonical_audit.json")
    parser.add_argument("--artifacts-dir", type=Path, default=ROOT / "output/shanay/runs")
    args = parser.parse_args(argv)
    artifacts = args.artifacts_dir.resolve() / uuid.uuid4().hex
    # F14 fix: create the run directory inside the guarded block so a startup
    # storage failure (e.g. FileExistsError, PermissionError) is captured in
    # the report rather than hiding its own evidence.  The output file is
    # written even when directory creation fails so callers always receive a
    # structured diagnostic from a non-zero exit code.
    def _guarded_build():
        artifacts.mkdir(parents=True, exist_ok=False)
        return build_report(args.package.resolve(), artifacts)
    report = guarded(_guarded_build)
    # Always leave a diagnostic, including absent packages/tools or unexpected
    # runtime errors; never convert missing prerequisites into success.
    # Guard output directory creation separately so a writable output path
    # can always receive the report even when the artifacts dir fails.
    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        write_atomic(args.output, json_bytes(report))
    except OSError as exc:
        # The filesystem cannot guarantee a saved report at an unwritable
        # destination. Keep the failure observable on stdout and exit nonzero.
        print(json.dumps({"report": None, "requested_report": str(args.output),
                          "task_gate": "failed", "index_ready": False,
                          "diagnostic_write_error": type(exc).__name__,
                          "audit_status": report.get("task_gate", report.get("status", "failed"))}))
        return 1
    print(
        json.dumps(
            {
                "report": str(args.output),
                "task_gate": report.get("task_gate", "failed"),
                "index_ready": False,
            }
        )
    )
    return 0 if report.get("task_gate") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
