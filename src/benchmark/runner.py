"""Resumable A-G experiment runner for FinRAG benchmarks (PRD R7/R12/R13).

What this runner guarantees, and what it deliberately does not:

* Resume integrity (F23): the manifest persists a full ``identity`` (code hash + git
  revision, benchmark data and eligible-case hashes, prompt, model-config content, index
  catalog, frozen controls, variant spec and the approved-gate set) and its hash is
  *recomputed from the saved content* on every open. A tampered file, a changed input, or a
  revoked/changed approval refuses the resume, listing exactly which identities changed.
* Honest states (F28): ``blocked`` (missing gates), ``blocked_no_engine`` (no provider/index
  wired), ``blocked_engine_mismatch`` (the injected engine is not the claimed variant),
  ``partial`` (some eligible cases attempted) and ``completed`` (every eligible case attempted
  through a validated engine). A refusal ledger from no engine is never written, so it can
  never be mistaken for, or resume into, a real run.
* Full denominators: the summary always reports eligible cases, attempted outputs and
  succeeded/refused/failed counts, whatever ``max_cases`` selected.
* Provenance (F26): runs over generated smoke fixtures report
  ``final_evaluation_status = BLOCKED_synthetic_smoke_fixture``.
* Benchmark context is NOT yet consumed by the engine (the engine queries its own index), so
  ``context_binding`` is reported as UNBOUND; no result may be called a source-equivalent
  benchmark experiment until a context-bound adapter exists.
"""

import hashlib
import json
import subprocess
import time
from dataclasses import asdict, dataclass, field
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

from .loaders import BenchmarkCase, assess_suite_provenance, load_benchmark, verify_gold_separation
from .metrics import compute_all_metrics

ROOT = Path(__file__).resolve().parents[2]

_BENCHMARK_FILES = {
    "financebench": "financebench_open150.json",
    "finqa": "finqa_candidate_universe.json",
    "tatqa": "tatqa_candidate_universe.json",
}


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


def _file_sha256(path: Path) -> str:
    """Hex SHA-256 of *path* contents, or 'missing' if it does not exist."""
    if not path.is_file():
        return "missing"
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _canonical_sha256(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _normalize_name(name: str) -> str:
    return name.strip().lower().replace("-", "").replace("_", "")


def _benchmark_data_path(benchmark_name: str) -> Path | None:
    normalized = _normalize_name(benchmark_name)
    for key, filename in _BENCHMARK_FILES.items():
        if key in normalized:
            return ROOT / "data" / "benchmarks" / filename
    return None


def _code_sha256() -> str:
    """Hash of every Python source file under src/ (relative path + bytes), in sorted order."""
    h = hashlib.sha256()
    for path in sorted((ROOT / "src").rglob("*.py")):
        h.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
        h.update(b"\0")
        h.update(path.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def _resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


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
    status: str  # "ready" or "blocked" at creation; run summaries carry the execution state
    identity: dict[str, Any] = field(default_factory=dict)

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
        data_path: Path | str | None = None,
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
        self.data_path = Path(data_path) if data_path is not None else None
        self.results_path = self.output_dir / "results.jsonl"
        self.manifest_path = self.output_dir / "run_manifest.json"
        self.summary_path = self.output_dir / "summary.json"

    # ------------------------------------------------------------------ identity
    def _suite(self) -> list[tuple[BenchmarkCase, Any]]:
        return load_benchmark(self.benchmark_name, self.data_path)

    def current_identity(self) -> dict[str, Any]:
        """Everything a resume must still agree with, recomputed from the actual artifacts."""
        data_path = self.data_path or _benchmark_data_path(self.benchmark_name)
        try:
            case_ids = [case.case_id for case, _ in self._suite()]
        except Exception:
            case_ids = []
        index_catalog = (self.settings.index_dir / "catalog.json") if self.settings else None
        return {
            "variant": self.variant,
            "benchmark": self.benchmark_name,
            "frozen_controls": dict(FROZEN_CONTROLS),
            "variant_spec": self.spec.to_dict(),
            "git_revision": get_git_revision(),
            "code_sha256": _code_sha256(),
            "benchmark_data_sha256": _file_sha256(data_path) if data_path else "unknown_benchmark",
            "eligible_case_count": len(case_ids),
            "eligible_case_ids_sha256": _canonical_sha256(case_ids),
            "prompt_template_sha256": _file_sha256(ROOT / "src" / "llm" / "prompts.py"),
            "model_config_path": self.model_config_path,
            "model_config_sha256": _file_sha256(_resolve(self.model_config_path)),
            "index_catalog_sha256": _file_sha256(index_catalog) if index_catalog else "unbound",
            "approved_gates": sorted(self.available_gates),
        }

    def init_or_validate_manifest(self) -> RunManifest:
        """Create a run manifest, or validate the saved one against the current actual state."""
        identity = self.current_identity()
        manifest_sha256 = _canonical_sha256(identity)

        if self.manifest_path.is_file():
            try:
                existing = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"Resumption rejected: {self.manifest_path} is not valid JSON.") from exc
            saved_identity = existing.get("identity")
            if not isinstance(saved_identity, dict) or not saved_identity:
                raise RuntimeError(
                    "Resumption rejected: saved manifest has no bound artifact identity "
                    "(legacy or edited); start a new run directory."
                )
            # The saved hash must describe the saved content (detects edited controls).
            if existing.get("manifest_sha256") != _canonical_sha256(saved_identity):
                raise RuntimeError(
                    "Resumption rejected: saved manifest content does not match its recorded hash "
                    f"in {self.manifest_path} (edited or corrupted)."
                )
            changed = sorted(k for k in set(identity) | set(saved_identity)
                             if identity.get(k) != saved_identity.get(k))
            if changed:
                raise RuntimeError(
                    f"Resumption rejected: current state differs from the saved run in {changed}. "
                    f"Saved hash: {existing.get('manifest_sha256')}, current hash: {manifest_sha256}"
                )
            return RunManifest(**existing)

        status = "ready" if self.manifest_validation["is_ready"] else "blocked"
        manifest = RunManifest(
            run_id=f"run_{self.variant}_{self.benchmark_name}_{int(time.time())}",
            variant=self.variant,
            benchmark=self.benchmark_name,
            created_at=datetime.now(UTC).isoformat(),
            git_revision=identity["git_revision"],
            frozen_controls=dict(FROZEN_CONTROLS),
            variant_spec=self.spec.to_dict(),
            manifest_sha256=manifest_sha256,
            is_ready=self.manifest_validation["is_ready"],
            missing_gates=self.manifest_validation["missing_gates"],
            model_profile=self.model_config_path,
            status=status,
            identity=identity,
        )
        self.manifest_path.write_text(json.dumps(manifest.to_dict(), indent=2), encoding="utf-8")
        return manifest

    # ------------------------------------------------------------------ engine checks
    def validate_engine(self) -> str:
        """Return '' when the injected engine verifiably implements this variant, else why not."""
        if self.engine is None:
            return "No engine (provider/index/model adapter) is connected."
        retriever = getattr(self.engine, "retriever", None)
        engine_variant = getattr(retriever, "variant", None)
        if engine_variant != self.variant:
            return (f"Engine retriever variant {engine_variant!r} is not the claimed variant "
                    f"{self.variant!r}; refusing to label its outputs {self.variant}.")
        if self.spec.requires_cross_encoder and getattr(retriever, "reranker", None) is None:
            return f"Variant {self.variant} requires a cross-encoder but the engine has none."
        return ""

    # ------------------------------------------------------------------ ledger
    def load_completed_case_ids(self) -> set[str]:
        """Read completed case IDs from existing results.jsonl."""
        completed = set()
        if self.results_path.is_file():
            with open(self.results_path, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            completed.add(json.loads(line)["case_id"])
                        except Exception:
                            pass
        return completed

    def _write_summary(self, summary: dict[str, Any]) -> dict[str, Any]:
        self.summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return summary

    def run(self, max_cases: int | None = None) -> dict[str, Any]:
        """Execute or resume benchmark evaluation; never report more than actually ran."""
        manifest = self.init_or_validate_manifest()
        identity = manifest.identity
        base = {
            "run_id": manifest.run_id,
            "variant": manifest.variant,
            "benchmark": manifest.benchmark,
            "git_revision": manifest.git_revision,
            "controls_hash": manifest.manifest_sha256,
            "eligible_cases": identity.get("eligible_case_count"),
            "context_binding": "UNBOUND: engine retrieves from its own index; benchmark contexts are not consumed.",
        }

        if not manifest.is_ready:
            return self._write_summary({
                **base,
                "status": "blocked",
                "message": f"Variant {manifest.variant} is blocked. Missing required gates: {manifest.missing_gates}",
                "missing_gates": manifest.missing_gates,
                "attempted_outputs": 0,
            })

        problem = self.validate_engine()
        if problem:
            status = "blocked_no_engine" if self.engine is None else "blocked_engine_mismatch"
            return self._write_summary({
                **base, "status": status, "message": problem, "attempted_outputs": 0,
                "note": "Dry/blocked: no case was attempted and no refusal ledger was written.",
            })

        suite = self._suite()
        eligible = len(suite)
        provenance = assess_suite_provenance(suite)
        gold_map = {case.case_id: gold for case, gold in suite}
        selected = suite[:max_cases] if max_cases is not None and max_cases > 0 else suite
        completed_ids = self.load_completed_case_ids()

        with open(self.results_path, "a", encoding="utf-8") as results_file:
            for case, _ in selected:
                if case.case_id in completed_ids:
                    continue
                eval_input = case.to_eval_input()
                if not verify_gold_separation(eval_input):
                    raise RuntimeError(f"Gold leaked in case {case.case_id}")

                start_time = time.monotonic()
                case_result = self._evaluate_single_case(case, eval_input)
                case_result["latency_seconds"] = round(time.monotonic() - start_time, 3)
                case_result["input_sha256"] = _canonical_sha256(eval_input)
                case_result["run_id"] = manifest.run_id
                case_result["variant"] = self.variant

                results_file.write(json.dumps(case_result) + "\n")
                results_file.flush()
                completed_ids.add(case.case_id)

        all_results = []
        with open(self.results_path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    all_results.append(json.loads(line))

        eval_metrics = compute_all_metrics(all_results, gold_map, eligible_cases=eligible)
        counts = {
            "ok": sum(1 for r in all_results if r.get("status") == "ok"),
            "refused": sum(1 for r in all_results
                           if r.get("status") in {"insufficient_evidence", "invalid_request", "index_not_ready"}),
            "failed": sum(1 for r in all_results if r.get("status") not in
                          {"ok", "insufficient_evidence", "invalid_request", "index_not_ready"}),
        }
        attempted = len(all_results)
        return self._write_summary({
            **base,
            "status": "completed" if attempted >= eligible else "partial",
            "attempted_outputs": attempted,
            "not_attempted": max(0, eligible - attempted),
            "outcome_counts": counts,
            "provenance": provenance,
            "final_evaluation_status": ("ELIGIBLE_authentic_source_bound" if provenance["full_evaluation_eligible"]
                                        else "BLOCKED_synthetic_smoke_fixture"),
            "ragas_status": "BLOCKED: no pinned RAGAS evaluator executed",
            "metrics": eval_metrics.summary(),
        })

    def _evaluate_single_case(self, case: BenchmarkCase, eval_input: dict[str, Any]) -> dict[str, Any]:
        """Evaluate one case through the validated engine, recording the stages that actually ran."""
        filters = {}
        ticker = case.metadata.get("ticker") if case.metadata else None
        if ticker:
            filters["ticker"] = ticker
        if case.fiscal_year:
            filters["fiscal_year"] = case.fiscal_year
        base = {"case_id": case.case_id, "benchmark": case.benchmark}

        try:
            engine_res = self.engine.answer_financial_question(
                question=case.question,
                filters=filters if filters else None,
            )
        except Exception as exc:
            return {**base, "status": "service_error", "answer": "",
                    "message": f"Engine execution exception: {type(exc).__name__}: {exc}",
                    "included_evidence_ids": [], "ranked_evidence_ids": []}

        trace = engine_res.get("retrieval_trace", {}) or {}
        stages = [s.get("stage") for s in trace.get("stages", []) if isinstance(s, dict)]
        record = {
            **base,
            "status": engine_res.get("status", "unknown"),
            "answer": engine_res.get("answer", ""),
            "message": engine_res.get("message", ""),
            "included_evidence_ids": engine_res.get("included_evidence_ids", []),
            "ranked_evidence_ids": trace.get("ranked_evidence_ids", engine_res.get("included_evidence_ids", [])),
            "evidence": engine_res.get("evidence", []),
            "calculations": engine_res.get("calculations", []),
            "engine_variant": trace.get("variant"),
            "engine_stages": stages,
        }
        # A variant label is not execution evidence: E/F/G need a recorded cross-encoder stage.
        if record["status"] == "ok":
            if trace.get("variant") != self.variant:
                record.update(status="service_error", answer="",
                              message=f"Engine trace variant {trace.get('variant')!r} != claimed {self.variant!r}.")
            elif self.spec.requires_cross_encoder and "cross_encoder_rerank" not in stages:
                record.update(status="service_error", answer="",
                              message="Variant requires a cross-encoder but no cross_encoder_rerank stage ran.")
        return record
