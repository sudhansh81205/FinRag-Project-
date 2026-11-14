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
    assert FROZEN_CONTROLS["generator_digest"] == "sha256:68ceab7e468a31c988b44d5a4984a0e21f58c4f7158c6ce29c1804babac38df7"


def test_frozen_controls_and_specs_are_deeply_immutable():
    """F23: Verify that FROZEN_CONTROLS and VARIANT_SPECS cannot be mutated."""
    with pytest.raises(TypeError):
        FROZEN_CONTROLS["max_passages"] = 999  # type: ignore[index]

    with pytest.raises(TypeError):
        VARIANT_SPECS["A"] = None  # type: ignore[index]


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


def test_verify_included_operands_canonical_plan_and_refusals():
    """F24: Verify canonical typed_calculator schema support and refusal of empty/malformed plans."""
    canonical_plan = {
        "issuer": "AAPL",
        "scope": "consolidated",
        "periods": [{"kind": "duration", "start": "2020-09-27", "end": "2021-09-25"}],
        "expression": {
            "op": "subtract",
            "args": [
                {"evidence_id": "cell_sales_2021"},
                {"evidence_id": "cell_cost_2021"},
            ],
        },
    }
    # Success when all cited operands are in included evidence
    valid, msg = verify_included_operands(canonical_plan, ["cell_sales_2021", "cell_cost_2021", "narrative_3"])
    assert valid is True
    assert msg == ""

    # Refusal when one cited operand is missing
    valid, msg = verify_included_operands(canonical_plan, ["cell_sales_2021", "narrative_3"])
    assert valid is False
    assert "cell_cost_2021" in msg

    # Empty plan must be refused
    valid, msg = verify_included_operands({}, ["cell_sales_2021"])
    assert valid is False
    assert "non-empty" in msg

    # Malformed / empty expression must be refused
    valid, msg = verify_included_operands({"expression": {}}, ["cell_sales_2021"])
    assert valid is False
    assert "empty or malformed" in msg
