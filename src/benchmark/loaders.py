"""Versioned benchmark loaders for FinQA, TAT-QA, and FinanceBench open 150.

Guarantees strict separation between evaluation input contexts and gold truth
references to prevent target leakage into model prompts and retrieval pipelines.

R7/R12, common A-G leakage-free experimental design (F33) and benchmark provenance
(F26). Input records are validated against an allowlisted schema; any gold/program/label
field found at *any* depth outside the dedicated ``gold`` object is refused. Records
also carry a provenance classification so that generated smoke fixtures can never be
mistaken for authentic official benchmark records.
"""

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DATA_BENCHMARKS = ROOT / "data" / "benchmarks"

# Fields that must never reach a prompt/retrieval input, at any nesting depth.
FORBIDDEN_INPUT_KEYS: frozenset[str] = frozenset({
    "gold", "gold_answer", "gold_value_numeric", "gold_program", "gold_evidence_ids",
    "gold_justification", "answer", "answers", "target", "targets", "label", "labels",
    "program", "derivation", "explanation", "rationale",
})

# Top-level keys an input record may carry besides the dedicated ``gold`` object.
_INPUT_RECORD_KEYS: frozenset[str] = frozenset({
    "case_id", "benchmark", "benchmark_version", "question", "company", "ticker",
    "fiscal_year", "doc_name", "question_type", "context_text", "context_tables",
    "gold", "provenance",
})

# Allow-listed metadata keys that are safe to expose in eval inputs (F33).
_SAFE_METADATA_KEYS: frozenset[str] = frozenset({"ticker"})

# Provenance keys an authentic, source-bound official record must declare (F26).
REQUIRED_PROVENANCE_KEYS: tuple[str, ...] = (
    "official_dataset", "official_id", "official_version", "split", "license", "source_sha256",
)


class BenchmarkInputError(ValueError):
    """A benchmark record violates the leakage-free input contract."""


def find_forbidden_keys(value: Any, path: str = "") -> list[str]:
    """Return the path of every forbidden key at any depth in dict/list structures."""
    found: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            here = f"{path}/{key}"
            if isinstance(key, str) and key.strip().lower() in FORBIDDEN_INPUT_KEYS:
                found.append(here)
            found.extend(find_forbidden_keys(child, here))
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            found.extend(find_forbidden_keys(child, f"{path}[{index}]"))
    return found


@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    benchmark: str
    version: str
    question: str
    company: str
    fiscal_year: str | None
    doc_name: str
    question_type: str
    context_text: tuple[str, ...] = field(default_factory=tuple)
    context_tables: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
    provenance_class: str = "synthetic_smoke_fixture"

    def to_eval_input(self) -> dict[str, Any]:
        """Return input context for the retriever/LLM. Strictly excludes gold answers."""
        eval_input = {
            "case_id": self.case_id,
            "benchmark": self.benchmark,
            "version": self.version,
            "question": self.question,
            "company": self.company,
            "fiscal_year": self.fiscal_year,
            "doc_name": self.doc_name,
            "question_type": self.question_type,
            "context_text": list(self.context_text),
            "context_tables": json.loads(json.dumps(list(self.context_tables))),
            "metadata": dict(self.metadata),
        }
        if not verify_gold_separation(eval_input):
            raise BenchmarkInputError(f"Gold or target field present in model input for {self.case_id}")
        return eval_input


@dataclass(frozen=True)
class GoldReference:
    case_id: str
    benchmark: str
    gold_answer: str | list[str]
    gold_value_numeric: float | None = None
    gold_program: dict[str, Any] | None = None
    gold_evidence_ids: tuple[str, ...] = field(default_factory=tuple)
    gold_justification: str | None = None
    relative_tolerance: float = 0.01  # 1% relative tolerance per PRD R7/R12
    zero_tolerance: float = 0.001  # declared absolute tolerance, in the gold's display unit


def verify_gold_separation(eval_input: Any) -> bool:
    """True only when no gold/program/label key exists at any depth of the model input."""
    return not find_forbidden_keys(eval_input)


def _validate_input_record(rec: dict[str, Any]) -> None:
    """Allowlisted input schema with recursive rejection of target fields (F33)."""
    if not isinstance(rec, dict):
        raise BenchmarkInputError("Benchmark record must be an object.")
    for required in ("case_id", "benchmark", "question"):
        if not isinstance(rec.get(required), str) or not rec[required].strip():
            raise BenchmarkInputError(f"Benchmark record is missing '{required}'.")
    unknown = sorted(set(rec) - _INPUT_RECORD_KEYS)
    if unknown:
        raise BenchmarkInputError(
            f"Case {rec['case_id']} has unallowlisted top-level fields {unknown}; "
            "add them to the input schema deliberately or remove them."
        )
    # The dedicated gold object is the only place a target may live.
    leaked = find_forbidden_keys({k: v for k, v in rec.items() if k not in {"gold"}})
    if leaked:
        raise BenchmarkInputError(f"Case {rec['case_id']} leaks target fields into model input: {leaked}")


def classify_provenance(rec: dict[str, Any]) -> str:
    """'authentic_source_bound' only when every required provenance key is declared."""
    prov = rec.get("provenance")
    if isinstance(prov, dict) and all(isinstance(prov.get(k), str) and prov[k].strip()
                                      for k in REQUIRED_PROVENANCE_KEYS):
        return "authentic_source_bound"
    return "synthetic_smoke_fixture"


def _parse_raw_record(rec: dict[str, Any]) -> tuple[BenchmarkCase, GoldReference]:
    _validate_input_record(rec)
    meta = {k: v for k, v in rec.items() if k in _SAFE_METADATA_KEYS}
    case = BenchmarkCase(
        case_id=rec["case_id"],
        benchmark=rec["benchmark"],
        version=rec.get("benchmark_version", "1.0.0"),
        question=rec["question"],
        company=rec.get("company", ""),
        fiscal_year=rec.get("fiscal_year"),
        doc_name=rec.get("doc_name", ""),
        question_type=rec.get("question_type", "general"),
        context_text=tuple(rec.get("context_text", [])),
        context_tables=tuple(rec.get("context_tables", [])),
        metadata=MappingProxyType(meta),
        provenance_class=classify_provenance(rec),
    )
    gold_data = rec.get("gold", {})
    gold = GoldReference(
        case_id=rec["case_id"],
        benchmark=rec["benchmark"],
        gold_answer=gold_data.get("gold_answer", ""),
        gold_value_numeric=gold_data.get("gold_value_numeric"),
        gold_program=gold_data.get("gold_program"),
        gold_evidence_ids=tuple(gold_data.get("gold_evidence_ids", [])),
        gold_justification=gold_data.get("gold_justification"),
    )
    case.to_eval_input()  # fail at load time, not at prompt time
    return case, gold


def _load(path: Path, label: str) -> list[tuple[BenchmarkCase, GoldReference]]:
    if not path.is_file():
        raise FileNotFoundError(f"{label} dataset file not found: {path}")
    return [_parse_raw_record(r) for r in json.loads(path.read_text(encoding="utf-8"))]


def load_financebench_open150(path: Path | str | None = None) -> list[tuple[BenchmarkCase, GoldReference]]:
    """Load the FinanceBench candidate file (synthetic smoke fixture unless provenance is declared)."""
    return _load(Path(path) if path is not None else DATA_BENCHMARKS / "financebench_open150.json", "FinanceBench")


def load_finqa(path: Path | str | None = None) -> list[tuple[BenchmarkCase, GoldReference]]:
    """Load the FinQA candidate file (synthetic smoke fixture unless provenance is declared)."""
    return _load(Path(path) if path is not None else DATA_BENCHMARKS / "finqa_candidate_universe.json", "FinQA")


def load_tatqa(path: Path | str | None = None) -> list[tuple[BenchmarkCase, GoldReference]]:
    """Load the TAT-QA candidate file (synthetic smoke fixture unless provenance is declared)."""
    return _load(Path(path) if path is not None else DATA_BENCHMARKS / "tatqa_candidate_universe.json", "TAT-QA")


def load_benchmark(name: str, path: Path | str | None = None) -> list[tuple[BenchmarkCase, GoldReference]]:
    """Unified entry point to load benchmark suites by name."""
    normalized = name.strip().lower().replace("-", "").replace("_", "")
    if "financebench" in normalized:
        return load_financebench_open150(path)
    if "finqa" in normalized:
        return load_finqa(path)
    if "tatqa" in normalized:
        return load_tatqa(path)
    raise ValueError(f"Unknown benchmark '{name}'. Supported: 'FinanceBench', 'FinQA', 'TAT-QA'")


def assess_suite_provenance(suite: list[tuple[BenchmarkCase, GoldReference]]) -> dict[str, Any]:
    """Quantify whether a loaded suite may be reported as authentic official benchmark data (F26).

    Count agreement never establishes validity: report duplicated questions/contexts and the
    number of records that declare complete official provenance. Anything short of every
    record being authentic is classed as a synthetic smoke fixture.
    """
    total = len(suite)
    authentic = sum(1 for case, _ in suite if case.provenance_class == "authentic_source_bound")
    questions = [case.question for case, _ in suite]
    contexts = [json.dumps([list(case.context_text), list(case.context_tables)], sort_keys=True)
                for case, _ in suite]
    golds = [json.dumps(gold.gold_answer, sort_keys=True) for _, gold in suite]
    return {
        "records": total,
        "authentic_source_bound_records": authentic,
        "unique_questions": len(set(questions)),
        "unique_contexts": len(set(contexts)),
        "unique_gold_answers": len(set(golds)),
        "classification": ("authentic_source_bound" if total and authentic == total
                           else "synthetic_smoke_fixture"),
        "full_evaluation_eligible": bool(total and authentic == total),
    }
