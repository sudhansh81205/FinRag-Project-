"""Versioned benchmark loaders for FinQA, TAT-QA, and FinanceBench open 150.

Guarantees strict separation between evaluation input contexts and gold truth
references to prevent target leakage into model prompts and retrieval pipelines.
"""

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DATA_BENCHMARKS = ROOT / "data" / "benchmarks"


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

    def to_eval_input(self) -> dict[str, Any]:
        """Return input context for the retriever/LLM. Strictly excludes gold answers."""
        return {
            "case_id": self.case_id,
            "benchmark": self.benchmark,
            "version": self.version,
            "question": self.question,
            "company": self.company,
            "fiscal_year": self.fiscal_year,
            "doc_name": self.doc_name,
            "question_type": self.question_type,
            "context_text": list(self.context_text),
            "context_tables": list(self.context_tables),
            "metadata": dict(self.metadata),
        }


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
    zero_tolerance: float = 0.001


def verify_gold_separation(eval_input: dict[str, Any]) -> bool:
    """Verify that no gold answer, program or target fields leaked into the eval input."""
    forbidden = {"gold", "gold_answer", "gold_program", "gold_evidence_ids", "gold_justification", "target", "label"}
    for k in forbidden:
        if k in eval_input:
            return False
    return True


def _parse_raw_record(rec: dict[str, Any]) -> tuple[BenchmarkCase, GoldReference]:
    meta = {k: v for k, v in rec.items() if k not in {
        "case_id", "benchmark", "benchmark_version", "question", "company",
        "fiscal_year", "doc_name", "question_type", "context_text", "context_tables", "gold"
    }}
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
    return case, gold


def load_financebench_open150(path: Path | str | None = None) -> list[tuple[BenchmarkCase, GoldReference]]:
    """Load the open 150 candidate universe for FinanceBench."""
    file_path = Path(path) if path is not None else DATA_BENCHMARKS / "financebench_open150.json"
    if not file_path.is_file():
        raise FileNotFoundError(f"FinanceBench dataset file not found: {file_path}")
    data = json.loads(file_path.read_text(encoding="utf-8"))
    return [_parse_raw_record(r) for r in data]


def load_finqa(path: Path | str | None = None) -> list[tuple[BenchmarkCase, GoldReference]]:
    """Load the FinQA candidate universe."""
    file_path = Path(path) if path is not None else DATA_BENCHMARKS / "finqa_candidate_universe.json"
    if not file_path.is_file():
        raise FileNotFoundError(f"FinQA dataset file not found: {file_path}")
    data = json.loads(file_path.read_text(encoding="utf-8"))
    return [_parse_raw_record(r) for r in data]


def load_tatqa(path: Path | str | None = None) -> list[tuple[BenchmarkCase, GoldReference]]:
    """Load the TAT-QA candidate universe."""
    file_path = Path(path) if path is not None else DATA_BENCHMARKS / "tatqa_candidate_universe.json"
    if not file_path.is_file():
        raise FileNotFoundError(f"TAT-QA dataset file not found: {file_path}")
    data = json.loads(file_path.read_text(encoding="utf-8"))
    return [_parse_raw_record(r) for r in data]


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
