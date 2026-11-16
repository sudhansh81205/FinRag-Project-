"""Canonical A-G experiment scaffold and immutable control contracts (Sudhansh Nov-12).

Provides immutable specifications, eligibility validation, complete context
contracts and prerequisite checks for controlled A-G evaluation.
"""

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

CANONICAL_VARIANTS: tuple[str, ...] = ("A", "B", "C", "D", "E", "F", "G")

# Controlled experiment baseline parameters common to all variants A-G
_RAW_FROZEN_CONTROLS: dict[str, Any] = {
    "embedding_model": "BAAI/bge-base-en-v1.5",
    "embedding_dim": 768,
    "vector_index": "exact_faiss_flat_ip",
    "generator_model": "gemma3:4b",
    "generator_digest": "sha256:68ceab7e468a31c988b44d5a4984a0e21f58c4f7158c6ce29c1804babac38df7",
    "max_passages": 5,
    "calculator": "restricted_decimal_trees",
    "numerical_relative_tolerance": 0.01,  # 1% relative tolerance
    "random_seed": 42,
}
FROZEN_CONTROLS: Mapping[str, Any] = MappingProxyType(_RAW_FROZEN_CONTROLS)


@dataclass(frozen=True)
class VariantSpec:
    variant_id: str
    name: str
    description: str
    narrative_representation: str  # "fixed_overlap" or "section_aware"
    table_representation: str      # "flattened_markdown" or "self_describing_cells"
    retrieval_mode: str            # "dense_only", "hybrid_rrf60", "hybrid_rrf60_cross_encoder", "routed_escalation"
    chart_tier_enabled: bool
    requires_cross_encoder: bool
    prerequisite_gates: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "variant_id": self.variant_id,
            "name": self.name,
            "description": self.description,
            "narrative_representation": self.narrative_representation,
            "table_representation": self.table_representation,
            "retrieval_mode": self.retrieval_mode,
            "chart_tier_enabled": self.chart_tier_enabled,
            "requires_cross_encoder": self.requires_cross_encoder,
            "prerequisite_gates": list(self.prerequisite_gates),
            "common_controls": dict(FROZEN_CONTROLS),
        }


_RAW_VARIANT_SPECS: dict[str, VariantSpec] = {
    "A": VariantSpec(
        variant_id="A",
        name="Dense baseline",
        description="Fixed overlapping narrative chunks and flattened Markdown tables, dense retrieval only",
        narrative_representation="fixed_overlap",
        table_representation="flattened_markdown",
        retrieval_mode="dense_only",
        chart_tier_enabled=False,
        requires_cross_encoder=False,
        prerequisite_gates=("fixed_overlap_index_representation",),
    ),
    "B": VariantSpec(
        variant_id="B",
        name="Section-aware chunks",
        description="Section-aware narrative chunks with flattened Markdown tables, dense retrieval only",
        narrative_representation="section_aware",
        table_representation="flattened_markdown",
        retrieval_mode="dense_only",
        chart_tier_enabled=False,
        requires_cross_encoder=False,
        prerequisite_gates=("section_aware_index_representation",),
    ),
    "C": VariantSpec(
        variant_id="C",
        name="Self-describing cells",
        description="Section-aware narratives, self-describing cells and parent table expansion, dense only",
        narrative_representation="section_aware",
        table_representation="self_describing_cells",
        retrieval_mode="dense_only",
        chart_tier_enabled=False,
        requires_cross_encoder=False,
        prerequisite_gates=("canonical_cells_and_parents",),
    ),
    "D": VariantSpec(
        variant_id="D",
        name="Hybrid dense/BM25 fusion",
        description="Dense + BM25 retrieval fused with reciprocal rank fusion (RRF k=60)",
        narrative_representation="section_aware",
        table_representation="self_describing_cells",
        retrieval_mode="hybrid_rrf60",
        chart_tier_enabled=False,
        requires_cross_encoder=False,
        prerequisite_gates=("canonical_cells_and_parents", "bm25_index"),
    ),
    "E": VariantSpec(
        variant_id="E",
        name="Hierarchical reranking",
        description="Hierarchical candidate restriction and bge-reranker-base cross-encoder scoring",
        narrative_representation="section_aware",
        table_representation="self_describing_cells",
        retrieval_mode="hybrid_rrf60_cross_encoder",
        chart_tier_enabled=False,
        requires_cross_encoder=True,
        prerequisite_gates=("canonical_cells_and_parents", "bm25_index", "bge_reranker_base"),
    ),
    "F": VariantSpec(
        variant_id="F",
        name="Bounded routing & escalation",
        description="Keyword + bounded routing with development-tuned escalation across text/table tiers",
        narrative_representation="section_aware",
        table_representation="self_describing_cells",
        retrieval_mode="routed_escalation",
        chart_tier_enabled=False,
        requires_cross_encoder=True,
        prerequisite_gates=("canonical_cells_and_parents", "bm25_index", "bge_reranker_base", "frozen_routing_thresholds"),
    ),
    "G": VariantSpec(
        variant_id="G",
        name="Approved chart descriptions",
        description="Independently approved source-linked chart descriptions added to candidate pool",
        narrative_representation="section_aware",
        table_representation="self_describing_cells",
        retrieval_mode="routed_escalation",
        chart_tier_enabled=True,
        requires_cross_encoder=True,
        prerequisite_gates=(
            "canonical_cells_and_parents",
            "bm25_index",
            "bge_reranker_base",
            "frozen_routing_thresholds",
            "independent_chart_approval",
        ),
    ),
}
VARIANT_SPECS: Mapping[str, VariantSpec] = MappingProxyType(_RAW_VARIANT_SPECS)


def get_variant_spec(variant_id: str) -> VariantSpec:
    """Retrieve immutable specification for a canonical variant A-G."""
    if variant_id not in VARIANT_SPECS:
        raise ValueError(
            f"Unknown variant '{variant_id}'. Supported canonical variants are: {', '.join(CANONICAL_VARIANTS)}"
        )
    return VARIANT_SPECS[variant_id]


def validate_experiment_manifest(spec: VariantSpec, available_gates: set[str] | None = None) -> dict[str, Any]:
    """Validate readiness of a variant against available gates."""
    available = set(available_gates or ())
    missing_gates = [g for g in spec.prerequisite_gates if g not in available]
    return {
        "variant_id": spec.variant_id,
        "is_ready": len(missing_gates) == 0,
        "required_gates": list(spec.prerequisite_gates),
        "missing_gates": missing_gates,
        "controls": dict(FROZEN_CONTROLS),
        "manifest_sha256": hashlib.sha256(
            json.dumps(spec.to_dict(), sort_keys=True).encode("utf-8")
        ).hexdigest(),
    }


_ALLOWED_OPS = frozenset({"add", "subtract", "multiply", "divide", "ratio_percent", "change", "percent_change"})
_MAX_NODES, _MAX_DEPTH = 31, 7


def _collect_validated_leaf_ids(root: Any) -> tuple[list[str] | None, str]:
    """Strictly validate an expression tree and return its cited leaf IDs (F24).

    Mirrors the authoritative typed evaluator's schema bounds: cited leaves are exactly
    {"evidence_id": str}; operators are exactly {"op", "args"} with an allowlisted op and
    two children (legacy {"type","value"} / {"type","name","operands"} nodes are accepted
    only with the same strictness). Unknown, malformed, oversized or too-deep nodes make the
    whole plan invalid rather than being silently ignored.
    """
    ids: list[str] = []
    nodes = 0

    def visit(node: Any, depth: int) -> str:
        nonlocal nodes
        nodes += 1
        if nodes > _MAX_NODES or depth > _MAX_DEPTH:
            return f"Expression exceeds {_MAX_NODES} nodes or depth {_MAX_DEPTH}."
        if not isinstance(node, dict):
            return "Expression node must be an object."
        keys = set(node)
        if keys == {"evidence_id"}:
            if not isinstance(node["evidence_id"], str) or not node["evidence_id"].strip():
                return "Evidence leaf must cite a nonempty string id."
            ids.append(node["evidence_id"])
            return ""
        if keys == {"type", "value"} and node["type"] == "leaf":
            if not isinstance(node["value"], str) or not node["value"].strip():
                return "Legacy leaf must cite a nonempty string id."
            ids.append(node["value"])
            return ""
        canonical = keys == {"op", "args"} and node["op"] in _ALLOWED_OPS
        legacy = (keys == {"type", "name", "operands"} and node["type"] == "operator"
                  and node["name"] in _ALLOWED_OPS)
        if not (canonical or legacy):
            return "Unknown or malformed expression node."
        children = node["args"] if canonical else node["operands"]
        if not isinstance(children, list) or len(children) != 2:
            return "Operators require exactly two operands."
        for child in children:
            problem = visit(child, depth + 1)
            if problem:
                return problem
        return ""

    problem = visit(root, 0)
    return (None, problem) if problem else (ids, "")


def verify_included_operands(calculation_plan: dict[str, Any], included_evidence_ids: list[str]) -> tuple[bool, str]:
    """Verify that every cited operand in a calculation plan is present in final included evidence.

    Supports canonical typed_calculator plans (issuer, scope, periods, expression) and bare
    expression nodes, plus the legacy leaf schema. Rejects empty, malformed, unknown-node,
    oversized or operand-free plans (F24).

    Returns (is_valid, error_message).
    """
    if not isinstance(calculation_plan, dict) or not calculation_plan:
        return False, "Calculation plan must be a non-empty dictionary."

    root = calculation_plan.get("expression", calculation_plan)
    if not isinstance(root, dict) or not root:
        return False, "Calculation plan contains an empty or malformed expression."

    operand_ids, problem = _collect_validated_leaf_ids(root)
    if operand_ids is None:
        return False, f"Calculation plan contains an empty or malformed expression: {problem}"
    if not operand_ids:
        return False, "Calculation plan contains no cited evidence operands."

    included_set = set(included_evidence_ids)
    missing = [oid for oid in operand_ids if oid not in included_set]
    if missing:
        return False, f"Calculation operand(s) not in included context: {missing}"
    return True, ""
