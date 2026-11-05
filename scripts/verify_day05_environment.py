"""Diagnose the Nov 3 environment boundary; keep failures and smoke artifacts."""

import argparse
import importlib.metadata
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
import urllib.request
import uuid
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.contracts import sha256, verify_parser_package  # noqa: E402


def run_command(arguments, *, cwd=ROOT, timeout=30, env=None):
    """No raw stderr in reports: credentials/remote responses may be reflected there."""
    try:
        result = subprocess.run(arguments, cwd=cwd, capture_output=True, text=True,
                                timeout=timeout, env=env, check=False)
        return {"status": "passed" if result.returncode == 0 else "failed",
                "returncode": result.returncode, "stdout": result.stdout.strip() if result.returncode == 0 else ""}
    except FileNotFoundError:
        return {"status": "blocked", "reason": "executable_not_found"}
    except subprocess.TimeoutExpired:
        return {"status": "failed", "reason": "command_timeout"}
    except OSError:
        return {"status": "failed", "reason": "command_unavailable"}


def package_info(module, distribution):
    try:
        available = importlib.util.find_spec(module) is not None
        version = importlib.metadata.version(distribution)
        return {"available": available, "version": version, "import_tested": False}
    except (ImportError, ValueError, importlib.metadata.PackageNotFoundError):
        return {"available": False, "version": None, "import_tested": False}


def guarded(check):
    try:
        return check()
    except Exception as exc:
        return {"status": "failed", "reason": "check_exception", "exception_type": type(exc).__name__}


def verify_parser_contract():
    return verify_parser_package(ROOT)


def dvc_smoke(directory: Path):
    """Restore a tiny fixture in a new local repo; never touch project data/cache."""
    if not package_info("dvc", "dvc")["available"]:
        return {"status": "blocked", "reason": "dvc_not_installed_in_current_interpreter"}
    directory.mkdir(parents=True, exist_ok=False)
    fixture = directory / "fixture.txt"
    fixture.write_text("source-checked fixture\n", encoding="utf-8")
    expected = sha256(fixture.read_bytes())
    environment = {**os.environ, "DVC_NO_ANALYTICS": "1"}
    commands = []
    for args in (("init", "--no-scm", "--quiet"), ("add", "fixture.txt", "--quiet")):
        command = [sys.executable, "-m", "dvc", *args]
        outcome = run_command(command, cwd=directory, timeout=120, env=environment)
        commands.append({"arguments": command, **outcome})
        if outcome["status"] != "passed":
            return {"status": "failed", "scope": "synthetic_fixture_only", "commands": commands}
    # This exact file was created above in a fresh owned directory.
    fixture.unlink()
    command = [sys.executable, "-m", "dvc", "checkout", "--quiet"]
    outcome = run_command(command, cwd=directory, timeout=120, env=environment)
    commands.append({"arguments": command, **outcome})
    actual = sha256(fixture.read_bytes()) if fixture.is_file() else None
    return {"status": "passed" if outcome["status"] == "passed" and actual == expected else "failed",
            "scope": "synthetic_fixture_only", "expected_sha256": expected, "restored_sha256": actual,
            "artifact_directory": str(directory), "commands": commands,
            "canonical_package_restore": "pending_Shanay_independent_validation"}


def mlflow_smoke(directory: Path, contract: dict):
    if contract.get("status") != "passed":
        return {"status": "blocked", "reason": "parser_contract_not_passed"}
    if not package_info("mlflow", "mlflow")["available"]:
        return {"status": "blocked", "reason": "mlflow_not_installed_in_current_interpreter"}
    from mlflow import MlflowClient

    directory.mkdir(parents=True, exist_ok=False)
    database = directory / "tracking.db"
    tracking_uri = f"sqlite:///{database.as_posix()}"
    client = MlflowClient(tracking_uri=tracking_uri)
    experiment = client.create_experiment("finrag-environment-smoke", artifact_location=(directory / "artifacts").as_uri())
    run = client.create_run(experiment, tags={"scope": "parser_contract_smoke_not_model_evaluation"})
    identity = run.info.run_id
    client.log_param(identity, "contract_version", "unified-2026-11-03")
    client.log_param(identity, "source_sha256", contract["source_sha256"])
    client.log_metric(identity, "records_checked", contract["record_count"])
    artifact = directory / "parser_contract.json"
    artifact.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
    client.log_artifact(identity, str(artifact))
    client.set_terminated(identity)
    # Reopen through another client and retrieve the stored artifact, not only in-memory state.
    reopened = MlflowClient(tracking_uri=tracking_uri)
    stored = reopened.get_run(identity)
    restored = Path(reopened.download_artifacts(identity, "parser_contract.json"))
    verified = (stored.info.status == "FINISHED"
                and stored.data.metrics.get("records_checked") == contract["record_count"]
                and stored.data.params.get("source_sha256") == contract["source_sha256"]
                and restored.read_bytes() == artifact.read_bytes())
    return {"status": "passed" if verified else "failed", "run_id": identity,
            "tracking_uri": tracking_uri, "artifact_directory": str(directory),
            "artifact_sha256": sha256(restored.read_bytes()), "readback_verified": verified,
            "scope": "persistent_local_smoke_not_generation_or_evaluation"}


def resource_inventory():
    info = {"platform": platform.platform(), "cpu_count": os.cpu_count(),
            "free_disk_bytes": shutil.disk_usage(ROOT).free,
            "memory_bytes": None, "gpu": "unknown", "gpu_memory_note": "OS-reported adapter memory is not usable model VRAM."}
    if os.name == "nt":
        for key, command in (
            ("memory_bytes", "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory | ConvertTo-Json"),
            ("gpu", "Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM | ConvertTo-Json"),
        ):
            result = run_command(["powershell", "-NoProfile", "-Command", command])
            if result["status"] == "passed":
                try:
                    info[key] = json.loads(result["stdout"])
                except ValueError:
                    pass
            else:
                info[f"{key}_check"] = result["status"]
    else:
        try:
            info["memory_bytes"] = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
        except (AttributeError, ValueError, OSError):
            pass
    return info


def ollama_inventory():
    """Read local model inventory only; never pull weights or call generation."""
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=3) as response:
            payload = json.load(response)
        return {"status": "reachable", "models": [{"name": model.get("name"), "digest": model.get("digest"),
                "size": model.get("size")} for model in payload["models"]], "generation_verified": False}
    except Exception:
        return {"status": "unavailable", "models": [], "generation_verified": False}


def build_report(artifacts: Path):
    revision = run_command(["git", "rev-parse", "HEAD"])
    dirty = run_command(["git", "status", "--porcelain"])
    contract = guarded(verify_parser_contract)
    report = {
        "schema_version": 2,
        "task": "Repair through Ujjwal November 3 environment boundary; not future task completion",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "revision": revision.get("stdout") or None,
        "worktree_dirty": bool(dirty["stdout"]) if dirty["status"] == "passed" else None,
        "python": {"executable": sys.executable, "version": platform.python_version()},
        "commands": {"git": run_command(["git", "--version"]),
                     "dvc": run_command([sys.executable, "-m", "dvc", "--version"])},
        "packages": {module: package_info(module, distribution) for module, distribution in (
            ("dvc", "dvc"), ("mlflow", "mlflow"), ("jsonschema", "jsonschema"),
            ("bs4", "beautifulsoup4"), ("lxml", "lxml"), ("faiss", "faiss-cpu"),
            ("docling", "docling"), ("sentence_transformers", "sentence-transformers"), ("torch", "torch"))},
        "resources": guarded(resource_inventory), "ollama": ollama_inventory(),
        "parser_contract": contract,
        "dvc_restore_smoke": guarded(lambda: dvc_smoke(artifacts / "dvc")),
        "mlflow_logging_smoke": guarded(lambda: mlflow_smoke(artifacts / "mlflow", contract)),
        "capacity_estimate": {"status": "blocked_pending_pilot",
            "formula": "sum(cases_per_suite * 7 * measured_seconds_per_case) / 3600 + extraction_hours + caption_hours + evaluator_hours",
            "missing_inputs": ["eligible case counts", "BGE/FAISS pilot", "Gemma/Ollama timing and hardware", "RAGAS timing", "machine availability"],
            "note": "No model calls or downloads; scheduled human hours are not machine capacity."},
    }
    report["environment_smoke_status"] = "passed" if all(report[key].get("status") == "passed" for key in (
        "parser_contract", "dvc_restore_smoke", "mlflow_logging_smoke")) else "blocked_or_failed"
    report["full_pipeline_ready"] = False
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "output/environment/report.json")
    parser.add_argument("--artifacts-dir", type=Path, default=ROOT / "output/environment/runs")
    args = parser.parse_args(argv)
    artifacts = args.artifacts_dir.resolve() / uuid.uuid4().hex
    artifacts.mkdir(parents=True, exist_ok=False)
    report = build_report(artifacts)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name(args.output.name + f".{uuid.uuid4().hex}.tmp")
    temporary.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, args.output)
    print(json.dumps({"report": str(args.output.resolve()), "status": report["environment_smoke_status"],
                      "full_pipeline_ready": False}, indent=2))
    return 0 if report["environment_smoke_status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
