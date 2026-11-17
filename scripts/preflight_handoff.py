"""R2/R4/R12/R13 common A-G runtime inventory, not project acceptance.

No downloads, daemon startup, model calls or human approvals are implicit.
Viva: installed weights, working inference and independently accepted results are different evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def check_model(profile, snapshot):
    """Compare installed identity with the frozen profile, never silently update it."""
    differences = [k for k in ("model", "digest", "quantization_level")
                   if not profile.get(k) or snapshot.get(k) != profile[k]]
    if "vision" in profile.get("capabilities", []) and "vision" not in snapshot.get("capabilities", []):
        differences.append("vision")
    return {"status": "blocked" if differences else "passed", "mismatches": differences,
            "installed": snapshot}


def local_endpoint(raw):
    url = urlsplit(raw)
    if (url.scheme != "http" or url.hostname not in {"127.0.0.1", "localhost", "::1"}
            or url.username or url.password or url.query or url.fragment or url.path not in {"", "/"}):
        raise ValueError("Use a local loopback Ollama origin without credentials, path or query.")
    return raw.rstrip("/")


def snapshot_identity(root):
    def git(*args):
        result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=10)
        return result.stdout.strip() if result.returncode == 0 else None
    try:
        return {"revision": git("rev-parse", "HEAD"), "dirty": bool(git("status", "--porcelain"))}
    except (OSError, subprocess.SubprocessError):
        return {"revision": None, "dirty": None}


def inventory(root=ROOT, *, profile_path=None, tokenizer_dir=None, probe_ollama=False, generate_smoke=False):
    from src.benchmark.gates import evaluate_gates

    root = Path(root)
    profile_path = Path(profile_path) if profile_path else root / "configs/gemma3-4b.json"
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    checks = {}
    checks["packages"] = {
        name: importlib.util.find_spec(name) is not None
        for name in ("requests", "numpy", "faiss", "transformers", "sentence_transformers", "pytest")
    }
    checks["ollama"] = {"status": "not_probed", "generation_executed": False}
    if probe_ollama or generate_smoke:
        try:
            from src.llm.ollama_profile import fingerprint
            endpoint = local_endpoint(profile.get("ollama_url", "http://127.0.0.1:11434"))
            checks["ollama"] = check_model(profile, fingerprint(endpoint, profile["model"], timeout=10))
            checks["ollama"]["generation_executed"] = False
            if generate_smoke and checks["ollama"]["status"] == "passed":
                from src.llm.client import UnifiedLLMClient
                client = UnifiedLLMClient.from_profile({**profile, "ollama_url": endpoint})
                result = client.generate("Reply with one short sentence stating that this is a runtime check.")
                checks["ollama"]["generation_executed"] = True
                checks["ollama"]["generation_status"] = result.get("status")
                checks["ollama"]["status"] = "passed" if result.get("success") else "blocked"
                # Prompt/output is a nonfinancial connectivity smoke, not benchmark evidence.
        except Exception as exc:
            checks["ollama"] = {"status": "blocked", "reason": type(exc).__name__,
                                 "generation_executed": False}
    checks["exact_index"] = {"status": "missing"}
    catalog = root / "data/index/bge-faiss/catalog.json"
    if catalog.is_file():
        try:
            from src.indexing.store import ExactStore
            store = ExactStore(catalog.parent)
            checks["exact_index"] = {"status": "passed", "records": len(store.records),
                                      "catalog_sha256": hashlib.sha256(catalog.read_bytes()).hexdigest()}
        except Exception as exc:
            checks["exact_index"] = {"status": "blocked", "reason": type(exc).__name__}
    checks["tokenizer"] = {"status": "missing"}
    if tokenizer_dir:
        try:
            from transformers import AutoTokenizer
            directory = Path(tokenizer_dir)
            tokenizer = AutoTokenizer.from_pretrained(directory, local_files_only=True, trust_remote_code=False)
            if not tokenizer.encode("Financial evidence.", add_special_tokens=True):
                raise ValueError("Empty tokenizer output")
            checks["tokenizer"] = {"status": "passed", "files_sha256": {
                str(p.relative_to(directory)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(directory.rglob("*")) if p.is_file()
            }}
        except Exception as exc:
            checks["tokenizer"] = {"status": "blocked", "reason": type(exc).__name__}
    checks["acceptance_gates"] = evaluate_gates(root, root / "docs/reports/2026-11-16_gate_acceptance.json")
    runtime_ready = (checks["ollama"]["status"] == "passed"
                     and checks["ollama"].get("generation_status") == "ok"
                     and checks["exact_index"]["status"] == "passed"
                     and checks["tokenizer"]["status"] == "passed")
    return {"schema_version": 1, "observed_at_utc": datetime.now(UTC).isoformat(),
            **snapshot_identity(root), "platform": platform.system(), "python": platform.python_version(),
            "profile_sha256": hashlib.sha256(profile_path.read_bytes()).hexdigest(),
            "checks": checks, "runtime_prerequisites_ready": runtime_ready,
            "full_project_complete": False,
            "scope": "Machine inventory only. Full A-G/context binding, independent reviews, results and release proof are separate.",
            "next": "Read docs/handoffs/RUSHIL_START_HERE.md; never edit acceptance marks to bypass a blocker."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path)
    parser.add_argument("--tokenizer-dir", type=Path)
    parser.add_argument("--probe-ollama", action="store_true", help="Read the local installed model identity; no generation")
    parser.add_argument("--generate-smoke", action="store_true", help="Explicitly run one real nonfinancial local generation")
    parser.add_argument("--output", type=Path, default=ROOT / "output/runtime-preflight.json")
    args = parser.parse_args()
    report = inventory(profile_path=args.profile, tokenizer_dir=args.tokenizer_dir,
                       probe_ollama=args.probe_ollama, generate_smoke=args.generate_smoke)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(args.output), "runtime_prerequisites_ready": report["runtime_prerequisites_ready"],
                      "full_project_complete": False}, indent=2))
    return 0 if report["runtime_prerequisites_ready"] else 2


if __name__ == "__main__":
    sys.exit(main())
