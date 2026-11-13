"""Canonical A-G experiment scaffold and immutable control contracts (Sudhansh Nov-12).

Provides immutable specifications, eligibility validation, complete context
contracts and prerequisite checks for controlled A-G evaluation.
"""

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


CANONICAL_VARIANTS: tuple[str, ...] = ("A", "B", "C", "D", "E", "F", "G")

# Controlled experiment baseline parameters common to all variants A-G
FROZEN_CONTROLS = {
    "embedding_model": "BAAI/bge-base-en-v1.5",
    "embedding_dim": 768,
    "vector_index": "exact_faiss_flat_ip",
    "generator_model": "gemma3:4b",
    "generator_digest": "sha256:751a0b6e9a781b0a5c43d99d10e0c90c74f76ca09fa496735e5a95b8719fb424",
    "max_passages": 5,
    "calculator": "restricted_decimal_trees",
    "numerical_relative_tolerance": 0.01,  # 1% relative tolerance
    "random_seed": 42,
}


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


VARIANT_SPECS: Mapping[str, VariantSpec] = {
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


def verify_included_operands(calculation_plan: dict[str, Any], included_evidence_ids: list[str]) -> tuple[bool, str]:
    """Verify that every cited operand in a calculation plan is present in final included evidence.

    Returns (is_valid, error_message).
    """
    if not isinstance(calculation_plan, dict):
        return False, "Calculation plan must be a dictionary."
    included_set = set(included_evidence_ids)

    def collect_leaf_ids(node: Any) -> list[str]:
        if not isinstance(node, dict):
            return []
        if node.get("type") == "leaf":
            val = node.get("value")
            return [str(val)] if val is not None else []
        ids = []
        for child in node.get("operands", []):
            ids.extend(collect_leaf_ids(child))
        return ids

    operand_ids = collect_leaf_ids(calculation_plan)
    missing = [oid for oid in operand_ids if oid not in included_set]
    if missing:
        return False, f"Calculation operand(s) not in included context: {missing}"
    return True, ""
