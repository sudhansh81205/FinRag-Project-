"""R13/common A-G: run repeatable local checks, preserving failures and blockers.

No downloads, source approvals or financial model calls are implicit. --live-runtime
explicitly enables one local model smoke and cached BGE query. This is not A-G evaluation.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def execute(name, command, directory, output, timeout=600):
    started = time.monotonic()
    status, code, detail = "failed", None, ""
    try:
        result = subprocess.run(command, cwd=directory, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=timeout)
        code = result.returncode
        detail = result.stdout + "\n" + result.stderr
        status = "passed" if code == 0 else "blocked" if name == "runtime" and code == 2 else "failed"
    except FileNotFoundError:
        status, detail = "blocked", "Executable is not available."
    except subprocess.TimeoutExpired:
        status, detail = "blocked", "Check exceeded its time limit; completion is not established."
    # Known credentials must not leak through a failing child/test message.
    for key in ("FINRAG_API_TOKEN", "FINRAG_BACKEND_TOKEN", "GEMINI_API_KEY", "HF_TOKEN"):
        value = os.environ.get(key)
        if value:
            detail = detail.replace(value, "[REDACTED]")
    log = output / f"{name}.txt"
    log.write_text(detail, encoding="utf-8")
    return {"name": name, "status": status, "returncode": code,
            "duration_seconds": round(time.monotonic() - started, 3), "log": str(log)}


def run_checks(output, *, live_runtime=False, tokenizer_dir=None, tokenizer_url=None,
               gguf=None, gguf_sha256=None, model_cache=None, root=ROOT):
    from src.benchmark.gates import evaluate_gates

    root, output = Path(root).resolve(), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    checks = []
    commands = [
        ("dependencies", [sys.executable, "-m", "pip", "check"], root),
        ("ruff", [sys.executable, "-m", "ruff", "check", "."], root),
        ("pytest", [sys.executable, "-m", "pytest", "-q"], root),
    ]
    node = shutil.which("node")
    if node:
        # Invoke Node directly: no Windows npm.cmd shell quoting or dependency install.
        commands.extend([
            ("web_syntax", [node, "--check", "public/app.js"], root / "web"),
            ("web_tests", [node, "--test", *[str(p.relative_to(root / "web"))
                                             for p in sorted((root / "web/tests").glob("*.test.mjs"))]], root / "web"),
        ])
    else:
        checks.append({"name": "web", "status": "blocked", "reason": "Node is unavailable."})
    preflight = [sys.executable, "scripts/preflight_handoff.py", "--output", str(output / "runtime.json")]
    if live_runtime:
        preflight += ["--probe-ollama", "--generate-smoke", "--probe-embedding"]
    if tokenizer_dir:
        preflight += ["--tokenizer-dir", str(Path(tokenizer_dir).resolve())]
    if tokenizer_url:
        preflight += ["--tokenizer-url", tokenizer_url, "--gguf", str(gguf), "--gguf-sha256", gguf_sha256]
    if model_cache:
        preflight += ["--model-cache", str(model_cache)]
    commands.extend([
        ("runtime", preflight, root),
        ("chart_integrity", [sys.executable, "scripts/verify_chart_set.py"], root),
        ("release_manifest", [sys.executable, "scripts/verify_release_package.py"], root),
    ])
    for name, command, directory in commands:
        record = execute(name, command, directory, output)
        checks.append(record)
        print(f"{name}: {record['status']}", flush=True)
    gates = evaluate_gates(root, root / "docs/reports/2026-11-16_gate_acceptance.json")
    report = {"observed_at_utc": datetime.now(UTC).isoformat(), "checks": checks,
              "acceptance_gates": gates, "live_runtime_requested": live_runtime,
              "all_commands_passed": all(c["status"] == "passed" for c in checks),
              "all_gates_open": all(g["open"] for g in gates.values()),
              "full_project_complete": False,
              "scope": "Automatic local checks only. Independent source/chart/output review, full experiments and submission remain separate."}
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "output/handoff-checks")
    parser.add_argument("--live-runtime", action="store_true")
    parser.add_argument("--tokenizer-dir", type=Path)
    parser.add_argument("--tokenizer-url")
    parser.add_argument("--gguf", type=Path)
    parser.add_argument("--gguf-sha256")
    parser.add_argument("--model-cache", type=Path)
    args = parser.parse_args()
    if args.live_runtime and not (args.tokenizer_dir or args.tokenizer_url and args.gguf and args.gguf_sha256):
        parser.error("--live-runtime requires the actual tokenizer directory or pinned GGUF service arguments.")
    if args.tokenizer_url and (not args.gguf or not args.gguf_sha256 or args.tokenizer_dir):
        parser.error("Choose one tokenizer: --tokenizer-dir or --tokenizer-url with --gguf and --gguf-sha256.")
    report = run_checks(args.output, live_runtime=args.live_runtime, tokenizer_dir=args.tokenizer_dir,
                        tokenizer_url=args.tokenizer_url, gguf=args.gguf, gguf_sha256=args.gguf_sha256,
                        model_cache=args.model_cache)
    return 0 if report["all_commands_passed"] and report["all_gates_open"] else 1


if __name__ == "__main__":
    sys.exit(main())
