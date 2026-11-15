"""Resumable A-G experiment runner for FinRAG benchmarks.

Features:
- Immutable control verification and refusal to resume on mutated controls.
- Variant gate validation (marks variants 'blocked' when prerequisite gates are missing).
- Resumable checkpointing via atomic JSONL logging.
- Gold answer isolation during execution.
- Metrics calculation (accuracy, recall, MRR, faithfulness, latencies, failure tracking).
- Support for secondary Llama comparison runs.
"""

import hashlib
import json
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.config import Settings
from src.pipeline.experiment_scaffold import (
    CANONICAL_VARIANTS,
    FROZEN_CONTROLS,
    get_variant_spec,
    validate_experiment_manifest,
)
from src.pipeline.finrag_engine import FinRAGEngine

from .loaders import BenchmarkCase, load_benchmark, verify_gold_separation
from .metrics import compute_all_metrics

ROOT = Path(__file__).resolve().parents[2]


def get_git_revision() -> str:
    """Get current git commit hash."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        return "unversioned"


@dataclass
class RunManifest:
    run_id: str
    variant: str
    benchmark: str
    created_at: str
    git_revision: str
    frozen_controls: dict[str, Any]
    variant_spec: dict[str, Any]
    manifest_sha256: str
    is_ready: bool
    missing_gates: list[str]
    model_profile: str
    status: str  # "ready", "blocked", "partial", "completed"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class BenchmarkRunner:
    def __init__(
        self,
        output_dir: Path | str,
        variant: str = "D",
        benchmark: str = "FinanceBench",
        model_config_path: Path | str | None = None,
        available_gates: set[str] | None = None,
        engine: FinRAGEngine | None = None,
        settings: Settings | None = None,
    ):
        if variant not in CANONICAL_VARIANTS:
            raise ValueError(f"Variant '{variant}' is not one of canonical {CANONICAL_VARIANTS}")
        self.variant = variant
        self.benchmark_name = benchmark
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.spec = get_variant_spec(variant)
        self.available_gates = set(available_gates or ())
        self.manifest_validation = validate_experiment_manifest(self.spec, self.available_gates)
        self.model_config_path = str(model_config_path) if model_config_path else "configs/gemma3-4b.json"
        self.engine = engine
        self.settings = settings
        self.results_path = self.output_dir / "results.jsonl"
        self.manifest_path = self.output_dir / "run_manifest.json"
        self.summary_path = self.output_dir / "summary.json"

    def init_or_validate_manifest(self) -> RunManifest:
        """Create a new run manifest or validate against existing for resumption."""
        git_rev = get_git_revision()
        timestamp = datetime.now(UTC).isoformat()
        
        manifest_data = {
            "variant": self.variant,
            "benchmark": self.benchmark_name,
            "frozen_controls": dict(FROZEN_CONTROLS),
            "variant_spec": self.spec.to_dict(),
            "model_profile": self.model_config_path,
        }
        manifest_sha256 = hashlib.sha256(
            json.dumps(manifest_data, sort_keys=True).encode("utf-8")
        ).hexdigest()

        if self.manifest_path.is_file():
            existing = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            # Refuse resumption if controls or variant specifications changed
            if existing.get("manifest_sha256") != manifest_sha256:
                raise RuntimeError(
                    f"Resumption rejected: run controls in {self.manifest_path} do not match current frozen controls. "
                    f"Saved hash: {existing.get('manifest_sha256')}, Current hash: {manifest_sha256}"
                )
            return RunManifest(**existing)

        status = "ready" if self.manifest_validation["is_ready"] else "blocked"
        manifest = RunManifest(
            run_id=f"run_{self.variant}_{self.benchmark_name}_{int(time.time())}",
            variant=self.variant,
            benchmark=self.benchmark_name,
            created_at=timestamp,
            git_revision=git_rev,
            frozen_controls=dict(FROZEN_CONTROLS),
            variant_spec=self.spec.to_dict(),
            manifest_sha256=manifest_sha256,
            is_ready=self.manifest_validation["is_ready"],
            missing_gates=self.manifest_validation["missing_gates"],
            model_profile=self.model_config_path,
            status=status,
        )
        self.manifest_path.write_text(json.dumps(manifest.to_dict(), indent=2), encoding="utf-8")
        return manifest

    def load_completed_case_ids(self) -> set[str]:
        """Read completed case IDs from existing results.jsonl."""
        completed = set()
        if self.results_path.is_file():
            with open(self.results_path, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            record = json.loads(line)
                            completed.add(record["case_id"])
                        except Exception:
                            pass
        return completed

    def run(self, max_cases: int | None = None) -> dict[str, Any]:
        """Execute or resume benchmark evaluation."""
        manifest = self.init_or_validate_manifest()

        if not manifest.is_ready:
            summary = {
                "run_id": manifest.run_id,
                "variant": manifest.variant,
                "benchmark": manifest.benchmark,
                "status": "blocked",
                "message": f"Variant {manifest.variant} is blocked. Missing required gates: {manifest.missing_gates}",
                "missing_gates": manifest.missing_gates,
                "total_cases": 0,
                "completed_cases": 0,
            }
            self.summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
            return summary

        # Load cases
        suite = load_benchmark(self.benchmark_name)
        if max_cases is not None and max_cases > 0:
            suite = suite[:max_cases]

        gold_map = {case.case_id: gold for case, gold in suite}
        completed_ids = self.load_completed_case_ids()

        with open(self.results_path, "a", encoding="utf-8") as results_file:
            for case, _ in suite:
                if case.case_id in completed_ids:
                    continue

                eval_input = case.to_eval_input()
                assert verify_gold_separation(eval_input), f"Gold leaked in case {case.case_id}"

                start_time = time.monotonic()
                case_result = self._evaluate_single_case(case, eval_input)
                case_result["latency_seconds"] = round(time.monotonic() - start_time, 3)

                results_file.write(json.dumps(case_result) + "\n")
                results_file.flush()
                completed_ids.add(case.case_id)

        # Compute summary metrics over all results in results.jsonl
        all_results = []
        with open(self.results_path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    all_results.append(json.loads(line))

        eval_metrics = compute_all_metrics(all_results, gold_map)
        summary = {
            "run_id": manifest.run_id,
            "variant": manifest.variant,
            "benchmark": manifest.benchmark,
            "status": "completed",
            "git_revision": manifest.git_revision,
            "controls_hash": manifest.manifest_sha256,
            "metrics": eval_metrics.summary(),
        }
        self.summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return summary

    def _evaluate_single_case(self, case: BenchmarkCase, eval_input: dict[str, Any]) -> dict[str, Any]:
        """Evaluate a single case against the configured engine or structured fallback."""
        question = case.question
        filters = {}
        if case.company:
            filters["company"] = case.company
        if case.fiscal_year:
            filters["fiscal_year"] = case.fiscal_year

        if self.engine is not None:
            try:
                engine_res = self.engine.answer_financial_question(
                    question=question,
                    filters=filters if filters else None,
                )
                return {
                    "case_id": case.case_id,
                    "benchmark": case.benchmark,
                    "status": engine_res.get("status", "unknown"),
                    "answer": engine_res.get("answer", ""),
                    "message": engine_res.get("message", ""),
                    "included_evidence_ids": engine_res.get("included_evidence_ids", []),
                    "ranked_evidence_ids": engine_res.get("retrieval_trace", {}).get("ranked_evidence_ids", engine_res.get("included_evidence_ids", [])),
                    "evidence": engine_res.get("evidence", []),
                    "calculations": engine_res.get("calculations", []),
                }
            except Exception as exc:
                return {
                    "case_id": case.case_id,
                    "benchmark": case.benchmark,
                    "status": "service_error",
                    "answer": "",
                    "message": f"Engine execution exception: {type(exc).__name__}: {exc}",
                    "included_evidence_ids": [],
                    "ranked_evidence_ids": [],
                }

        # If no live engine was passed (e.g. offline dry run / candidate check)
        return {
            "case_id": case.case_id,
            "benchmark": case.benchmark,
            "status": "insufficient_evidence",
            "answer": "",
            "message": "Offline benchmark evaluation: no live search engine or provider connected.",
            "included_evidence_ids": [],
            "ranked_evidence_ids": [],
        }
