"""Candidate chart-set integrity, source resolution and split checks; no model calls."""

import hashlib
import json
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

from .questions import audit_questions


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON key in chart data or review ledger.")
            result[key] = value
        return result

    def invalid(_value):
        raise ValueError("Non-finite JSON number in chart data or review ledger.")

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)


def case_fingerprint(case):
    """Bind review to the entire unchanged candidate, including image and split."""
    return sha(json.dumps(case, sort_keys=True, ensure_ascii=False,
                          separators=(",", ":"), allow_nan=False).encode("utf-8"))


def local(root, relative):
    if not isinstance(relative, str):
        raise ValueError("A relative dataset path is required.")
    path = root / relative
    if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("Dataset path escapes its root.")
    return path


def load_candidate_set(directory):
    directory = Path(directory)
    index = read_json((directory / "question-set.json").read_bytes())
    manifest_path = local(directory, index["source_manifest"])
    manifest = read_json(manifest_path.read_bytes())
    records = manifest["sources"]
    if len({s["source_asset_id"] for s in records}) != len(records):
        raise ValueError("Duplicate chart source identity.")
    if len({s["image_sha256"] for s in records}) != len(records):
        raise ValueError("Duplicate original chart asset.")
    sources = {s["source_asset_id"]: s for s in records}
    for source in records:
        asset = local(directory, source["asset"])
        if sha(asset.read_bytes()) != source["image_sha256"]:
            raise ValueError("Original chart asset checksum mismatch.")
        if not all(source.get(k) for k in ("accession", "company", "page", "pdf_sha256", "pdf_url", "source_locator")):
            raise ValueError("Chart source lacks filing provenance.")
    cases, file_hashes = [], {}
    for name in index["question_files"]:
        raw = local(directory, name).read_bytes()
        file_hashes[name] = sha(raw)
        cases.extend(read_json(raw))
    if file_hashes != index["question_files_sha256"]:
        raise ValueError("Frozen candidate question file checksum mismatch.")
    if file_hashes["apple-2021-candidate-questions.json"] != index["dev_file_sha256_unchanged"]:
        raise ValueError("Existing development questions changed.")
    for case in cases:
        source = sources.get(case["source_asset_id"])
        if source is None or source["image_sha256"] != case["image_sha256"]:
            raise ValueError("Question does not resolve to its original chart.")
        if case["original_image_group"] != source["original_image_group"]:
            raise ValueError("Question and source duplicate groups differ.")
    audit = audit_questions(cases)
    if audit["counts"] != index["target"] or len(cases) != 50:
        raise ValueError("Candidate set must contain exactly 15 dev and 35 heldout questions.")
    by_source = {identity: sum(q["source_asset_id"] == identity for q in cases) for identity in sources}
    if not all(by_source.values()):
        raise ValueError("Unused source in frozen question manifest.")
    return cases, manifest, {**audit, "total": len(cases), "question_files_sha256": file_hashes,
                             "source_manifest_sha256": sha(manifest_path.read_bytes()),
                             "question_counts_by_source": by_source,
                             "asset_hashes_checked": len(sources),
                             "heldout_answers_generated_or_scored": False,
                             "scope": "Candidate image/question integrity; not independent label approval or A-G evaluation."}


def load_reviewed_set(directory, approvals_path, *, trusted_reviewers, label_authors):
    """Validate a separate human review ledger without rewriting frozen labels.

    Reviewer identities and original label authors are caller-owned trust inputs,
    never accepted solely from an approval file. This validates recorded approval
    provenance, not a human's identity or visual judgement; the review must really
    be performed and authenticated through the team's review process. It cannot
    approve model captions or certify the full application/evaluation experiment.
    """
    if isinstance(trusted_reviewers, str) or isinstance(label_authors, str):
        raise ValueError("Reviewer and author identities must be explicit collections.")
    reviewers, authors = set(trusted_reviewers), set(label_authors)
    if (not reviewers or not authors
            or any(not isinstance(name, str) or not name.strip() for name in reviewers | authors)):
        raise ValueError("Named trusted reviewers and known label authors are required.")
    directory = Path(directory)
    cases, manifest, audit = load_candidate_set(directory)
    approval_bytes = Path(approvals_path).read_bytes()
    ledger = read_json(approval_bytes)
    if not isinstance(ledger, dict):
        raise ValueError("Approval ledger must be a JSON object.")
    expected_binding = {"question_set_sha256": sha((directory / "question-set.json").read_bytes()),
                        "question_files_sha256": audit["question_files_sha256"],
                        "source_manifest_sha256": audit["source_manifest_sha256"]}
    if ledger.get("schema_version") != 1 or ledger.get("candidate_binding") != expected_binding:
        raise ValueError("Approval ledger does not bind the unchanged frozen candidate set.")
    reviewer = ledger.get("reviewer_identity")
    if reviewer not in reviewers or reviewer in authors:
        raise ValueError("Approval requires a trusted independent reviewer, not a label author.")
    try:
        reviewed_at = datetime.fromisoformat(ledger["reviewed_at"])
        if reviewed_at.tzinfo is None or reviewed_at > datetime.now(UTC):
            raise ValueError("Missing time zone")
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Approval requires an ISO review timestamp with time zone.") from exc
    if ledger.get("method") != "human_original_image_and_source":
        raise ValueError("Approval requires recorded original-image and source review.")
    decisions = ledger.get("decisions")
    if not isinstance(decisions, list) or len(decisions) != len(cases):
        raise ValueError("Every frozen question requires one independent decision.")
    decisions_by_id = {}
    for decision in decisions:
        if not isinstance(decision, dict) or decision.get("id") in decisions_by_id:
            raise ValueError("Invalid or duplicate independent decision.")
        decisions_by_id[decision.get("id")] = decision
    if set(decisions_by_id) != {case["id"] for case in cases}:
        raise ValueError("Approval decision identities differ from the frozen question set.")
    reviewed = []
    for case in cases:
        decision = decisions_by_id[case["id"]]
        if (decision.get("case_sha256") != case_fingerprint(case)
                or decision.get("decision") != "passed"
                or decision.get("original_image_checked") is not True
                or decision.get("source_provenance_checked") is not True
                or not isinstance(decision.get("basis"), str) or not decision["basis"].strip()):
            raise ValueError(f"Missing, rejected or stale independent approval for {case['id']}.")
        promoted = deepcopy(case)
        promoted["independent_review"] = "passed"
        promoted["review"] = {"reviewer_identity": reviewer,
                              "reviewed_at": ledger["reviewed_at"],
                              "basis": decision["basis"], "approval_sha256": sha(approval_bytes)}
        reviewed.append(promoted)
    return reviewed, manifest, {**audit, "status": "independently_reviewed_labels",
                                "independent_review": "passed", "evaluation_ready": True,
                                "approval_sha256": sha(approval_bytes), "reviewer_identity": reviewer,
                                "label_authors": sorted(authors),
                                "trusted_reviewers_at_load": sorted(reviewers),
                                "chart_descriptions_approved": False,
                                "scope": "Hash-bound recorded human label approvals only; no caption approval, model run or full A-G acceptance."}
