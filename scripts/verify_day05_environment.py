"""Verify the unified PRD's Nov 3 environment and handoff gates."""

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_RECORD_FIELDS = {
    "id",
    "content",
    "metadata",
}
REQUIRED_METADATA_FIELDS = {
    "accession",
    "source_locator",
    "source_sha256",
    "type",
}


def command_version(command: str) -> str | None:
    executable = shutil.which(command)
    if not executable:
        return None
    result = subprocess.run(
        [executable, "--version"], capture_output=True, text=True, check=False
    )
    return (result.stdout or result.stderr).strip() or "installed"


def dvc_command(*arguments: str) -> list[str]:
    executable = shutil.which("dvc")
    return [executable, *arguments] if executable else [sys.executable, "-m", "dvc", *arguments]


def verify_parser_contract() -> dict:
    output = ROOT / "data/processed/apple-2021"
    manifest = json.loads((ROOT / "data/filing_manifest.json").read_text(encoding="utf-8"))
    records = []
    for filename in ("narrative.jsonl", "tables.jsonl"):
        path = output / filename
        if not path.is_file():
            return {"status": "blocked", "reason": f"missing {path.relative_to(ROOT)}"}
        records.extend(
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    failures = []
    for record in records:
        if not REQUIRED_RECORD_FIELDS <= record.keys():
            failures.append("record fields")
            break
        if not REQUIRED_METADATA_FIELDS <= record["metadata"].keys():
            failures.append("metadata fields")
            break
        if record["metadata"]["accession"] != manifest["accession"]:
            failures.append("accession mismatch")
            break
    return {
        "status": "passed" if not failures else "failed",
        "record_count": len(records),
        "accession": manifest["accession"],
        "source_sha256": manifest["raw_sha256"],
        "record_ids_sha256": hashlib.sha256(
            "\n".join(sorted(record["id"] for record in records)).encode()
        ).hexdigest(),
        "failure": failures[0] if failures else None,
    }


def dvc_smoke() -> dict:
    if importlib.util.find_spec("dvc") is None and not shutil.which("dvc"):
        return {"status": "blocked", "reason": "dvc executable is not installed"}
    os.environ["DVC_NO_ANALYTICS"] = "1"
    with tempfile.TemporaryDirectory(prefix="finrag-dvc-", ignore_cleanup_errors=True) as directory:
        root = Path(directory)
        fixture = root / "fixture.txt"
        fixture.write_text("source-checked fixture\n", encoding="utf-8")
        commands = [
            dvc_command("init", "--no-scm", "--quiet"),
            dvc_command("add", "fixture.txt", "--quiet"),
        ]
        for command in commands:
            result = subprocess.run(command, cwd=root, capture_output=True, text=True)
            if result.returncode:
                return {"status": "failed", "command": command, "error": result.stderr[-500:]}
        expected = hashlib.sha256(fixture.read_bytes()).hexdigest()
        fixture.unlink()
        result = subprocess.run(
            dvc_command("checkout", "--quiet"), cwd=root, capture_output=True, text=True
        )
        if result.returncode or not fixture.is_file():
            return {"status": "failed", "command": ["dvc", "checkout"], "error": result.stderr[-500:]}
        return {
            "status": "passed" if hashlib.sha256(fixture.read_bytes()).hexdigest() == expected else "failed",
            "restored_sha256": hashlib.sha256(fixture.read_bytes()).hexdigest(),
        }


def mlflow_smoke() -> dict:
    if importlib.util.find_spec("mlflow") is None:
        return {"status": "blocked", "reason": "mlflow package is not installed"}
    import mlflow

    with tempfile.TemporaryDirectory(prefix="finrag-mlflow-") as directory:
        os.environ["MLFLOW_ALLOW_FILE_STORE"] = "true"
        tracking_uri = (Path(directory) / "runs").as_uri()
        mlflow.set_tracking_uri(tracking_uri)
        with mlflow.start_run(run_name="finrag-day05-smoke") as run:
            mlflow.log_param("contract_version", "unified-2026-11-03")
            mlflow.log_metric("records_checked", verify_parser_contract()["record_count"])
            run_id = run.info.run_id
        stored = mlflow.get_run(run_id)
        return {
            "status": "passed",
            "run_id": run_id,
            "tracking_uri": tracking_uri,
            "contract_version": stored.data.params["contract_version"],
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "docs/reports/2026-11-03_day-05_environment.json",
    )
    args = parser.parse_args()
    packages = {}
    for name in ("dvc", "mlflow", "faiss", "docling", "sentence_transformers", "torch"):
        packages[name] = bool(importlib.util.find_spec(name))
    report = {
        "schema_version": 1,
        "task": "2026-11-03 Ujjwal: verify environment resources and handoff contracts",
        "revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "commands": {
            "python": command_version("python"),
            "dvc": (
                command_version("dvc")
                or subprocess.check_output(dvc_command("--version"), text=True).strip()
            ),
            "git": command_version("git"),
        },
        "packages": packages,
        "parser_contract": verify_parser_contract(),
        "dvc_restore_smoke": dvc_smoke(),
        "mlflow_logging_smoke": mlflow_smoke(),
        "capacity_estimate": {
            "status": "blocked_pending_pilot",
            "formula": "(cases * variants * observed_seconds_per_case / 3600) + extraction + captioning + evaluator_overhead",
            "missing_inputs": [
                "BGE/FAISS representative pilot timing",
                "Gemma 3/Ollama hardware timing",
                "RAGAS faithfulness timing",
                "final A-G case and variant counts"
            ],
            "do_not_claim": "Full evaluation capacity is not established by this environment check."
        }
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if report["parser_contract"]["status"] != "passed":
        raise SystemExit(1)
    if report["dvc_restore_smoke"]["status"] != "passed":
        raise SystemExit(1)
    if report["mlflow_logging_smoke"]["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
