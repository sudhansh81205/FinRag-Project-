"""Tests for canonical A-G experiment scaffold and immutable control contracts."""

import pytest

from src.pipeline.experiment_scaffold import (
    CANONICAL_VARIANTS,
    FROZEN_CONTROLS,
    VARIANT_SPECS,
    get_variant_spec,
    validate_experiment_manifest,
    verify_included_operands,
)


def test_canonical_variants_cover_a_to_g():
    assert CANONICAL_VARIANTS == ("A", "B", "C", "D", "E", "F", "G")
    assert all(v in VARIANT_SPECS for v in CANONICAL_VARIANTS)


def test_variant_specs_are_immutable():
    spec = get_variant_spec("D")
    assert spec.variant_id == "D"
    assert spec.retrieval_mode == "hybrid_rrf60"
    with pytest.raises(Exception):
        spec.variant_id = "Z"


def test_unknown_variant_rejected():
    with pytest.raises(ValueError, match="Unknown variant"):
        get_variant_spec("Z")


def test_frozen_controls_guarantee_common_settings():
    assert FROZEN_CONTROLS["max_passages"] == 5
    assert FROZEN_CONTROLS["embedding_model"] == "BAAI/bge-base-en-v1.5"
    assert FROZEN_CONTROLS["embedding_dim"] == 768
    assert FROZEN_CONTROLS["numerical_relative_tolerance"] == 0.01


def test_manifest_validation_detects_missing_gates():
    spec_e = get_variant_spec("E")
    manifest = validate_experiment_manifest(spec_e, available_gates={"canonical_cells_and_parents"})
    assert manifest["is_ready"] is False
    assert "bge_reranker_base" in manifest["missing_gates"]
    assert "bm25_index" in manifest["missing_gates"]

    ready_manifest = validate_experiment_manifest(
        spec_e,
        available_gates={"canonical_cells_and_parents", "bm25_index", "bge_reranker_base"},
    )
    assert ready_manifest["is_ready"] is True
    assert len(ready_manifest["missing_gates"]) == 0


def test_variant_g_requires_independent_chart_approval():
    spec_g = get_variant_spec("G")
    assert "independent_chart_approval" in spec_g.prerequisite_gates
    assert spec_g.chart_tier_enabled is True

    manifest = validate_experiment_manifest(
        spec_g,
        available_gates={
            "canonical_cells_and_parents",
            "bm25_index",
            "bge_reranker_base",
            "frozen_routing_thresholds",
        },
    )
    assert manifest["is_ready"] is False
    assert manifest["missing_gates"] == ["independent_chart_approval"]


def test_verify_included_operands_success_and_refusal():
    plan = {
        "type": "operator",
        "name": "subtract",
        "operands": [
            {"type": "leaf", "value": "fact_sales_2021"},
            {"type": "leaf", "value": "fact_cost_2021"},
        ],
    }
    # Success when both operands are in included evidence
    valid, msg = verify_included_operands(plan, ["fact_sales_2021", "fact_cost_2021", "narrative_1"])
    assert valid is True
    assert msg == ""

    # Failure when an operand was excluded by context budget
    valid, msg = verify_included_operands(plan, ["fact_sales_2021", "narrative_1"])
    assert valid is False
    assert "fact_cost_2021" in msg
