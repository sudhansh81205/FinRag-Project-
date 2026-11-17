"""Prerequisite-gate evaluation bound to actual artifacts and explicit human acceptance (F34).

R1/R2/R7/R11/R12/R13, common A-G readiness. A report flag, a corpus-status string or a
chart "promotion" boolean is a *claim about* an artifact, not the artifact. A gate opens only
when ALL hold:

1. an acceptance record exists naming an accepting person, a timestamp and, per gate, the
   SHA-256 of each artifact the gate depends on (no record -> no gate; nothing is synthesized);
2. every listed artifact exists now and re-hashes to the recorded value (missing, tampered or
   stale artifacts close the gate on every call, including on resume);
3. gate-specific validation passes against the actual files (for charts: the frozen
   ``load_reviewed_set`` check with a reviewer who is not a label author).

Candidate evidence (corpus audit, chart ledger, frozen manifest) is reported separately and
never opens a gate by itself. Viva: why can a submitter's status string not replace the
artifact it describes?
"""

import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ACCEPTANCE_PATH = ROOT / "docs" / "reports" / "2026-11-16_gate_acceptance.json"

ALL_GATES: tuple[str, ...] = (
    "fixed_overlap_index_representation",
    "section_aware_index_representation",
    "canonical_cells_and_parents",
    "bm25_index",
    "bge_reranker_base",
    "frozen_routing_thresholds",
    "independent_chart_approval",
)


def _sha256_file(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def load_acceptance(path: Path | str | None = None) -> tuple[dict[str, Any] | None, str]:
    path = Path(path) if path else DEFAULT_ACCEPTANCE_PATH
    if not path.is_file():
        return None, f"No acceptance record at {path}."
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None, "Acceptance record is not valid JSON."
    if not (isinstance(record, dict) and isinstance(record.get("accepted_by"), str)
            and record["accepted_by"].strip() and isinstance(record.get("accepted_at"), str)
            and isinstance(record.get("gates"), dict)):
        return None, "Acceptance record lacks accepted_by/accepted_at/gates."
    return record, ""


def _check_artifacts(gate_record: Any, root: Path) -> list[str]:
    problems = []
    artifacts = gate_record.get("artifacts") if isinstance(gate_record, dict) else None
    if not isinstance(artifacts, dict) or not artifacts:
        return ["Gate lists no bound artifacts."]
    for rel, expected in artifacts.items():
        if (not isinstance(rel, str) or not rel or "\\" in rel or ":" in rel
                or PurePosixPath(rel).is_absolute() or ".." in PurePosixPath(rel).parts
                or not isinstance(expected, str) or not re.fullmatch(r"[a-f0-9]{64}", expected)):
            problems.append("Invalid artifact path or SHA-256.")
            continue
        target = (root / rel)
        if not target.resolve().is_relative_to(root.resolve()):
            problems.append(f"Artifact escapes project root: {rel}")
            continue
        actual = _sha256_file(target)
        if actual is None:
            problems.append(f"Artifact missing: {rel}")
        elif actual != expected:
            problems.append(f"Artifact changed since acceptance: {rel}")
    return problems


def _validate_chart_gate(gate_record: dict[str, Any], root: Path) -> list[str]:
    """Re-run the frozen chart-ledger validation with the accepted reviewer/author identities."""
    from src.charts.dataset import load_reviewed_set

    reviewers, authors = gate_record.get("trusted_reviewers"), gate_record.get("label_authors")
    approvals = gate_record.get("approvals_path")
    if not (isinstance(reviewers, list) and isinstance(authors, list) and isinstance(approvals, str)):
        return ["Chart gate needs trusted_reviewers, label_authors and approvals_path."]
    paths = [approvals, gate_record.get("captions_path"), gate_record.get("caption_approvals_path")]
    if any(not isinstance(path, str) or path not in gate_record.get("artifacts", {}) for path in paths):
        return ["Chart gate must hash-bind question approvals, caption candidates and separate caption decisions."]
    try:
        load_reviewed_set(root / "data" / "charts", root / approvals,
                          trusted_reviewers=reviewers, label_authors=authors)
        from src.charts.approval import load_reviewed_captions
        load_reviewed_captions(root / paths[1], root / paths[2], root / "data/charts",
                               trusted_reviewers=reviewers,
                               caption_authors=gate_record.get("caption_authors", []))
    except Exception as exc:
        return [f"Chart ledger validation failed: {exc}"]
    return []


def evaluate_gates(root: Path | str = ROOT, acceptance_path: Path | str | None = None) -> dict[str, dict[str, Any]]:
    """Per-gate ``{"open": bool, "reasons": [...]}`` derived from actual artifacts and acceptance."""
    root = Path(root)
    acceptance, why_not = load_acceptance(acceptance_path)
    report: dict[str, dict[str, Any]] = {}
    for gate in ALL_GATES:
        reasons: list[str] = []
        if acceptance is None:
            reasons.append(why_not)
        else:
            gate_record = acceptance["gates"].get(gate)
            if gate_record is None:
                reasons.append("Gate is not listed in the acceptance record.")
            else:
                reasons.extend(_check_artifacts(gate_record, root))
                if gate == "independent_chart_approval" and not reasons:
                    reasons.extend(_validate_chart_gate(gate_record, root))
                if gate == "frozen_routing_thresholds" and not reasons:
                    thresholds = (gate_record.get("thresholds") or "unfrozen")
                    try:
                        from src.retrieval.bm25 import RoutingPolicy
                        if not isinstance(thresholds, dict) or set(thresholds) != {
                            "min_candidates", "max_tiers", "min_cross_encoder_score"}:
                            raise ValueError("Missing explicit thresholds")
                        RoutingPolicy(**thresholds)
                    except (TypeError, ValueError):
                        reasons.append("Routing thresholds are not frozen as a valid explicit policy.")
        report[gate] = {"open": not reasons, "reasons": reasons}
    return report


def detect_available_gates(root: Path | str = ROOT, acceptance_path: Path | str | None = None) -> set[str]:
    """Gates that are open right now; recomputed from the artifacts on every call."""
    return {gate for gate, info in evaluate_gates(root, acceptance_path).items() if info["open"]}
