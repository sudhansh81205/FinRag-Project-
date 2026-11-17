"""R11/G: verify separately recorded caption decisions against original assets.

This validates a real review record supplied by an eligible person. It neither
authenticates that person nor creates their decision. Question-label acceptance
alone never licenses a generated caption.
"""
import copy
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from src.charts.caption import validate_description
from src.charts.dataset import read_json


def caption_fingerprint(caption):
    return hashlib.sha256(json.dumps(caption, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load_reviewed_captions(captions_path, approvals_path, chart_root, *, trusted_reviewers, caption_authors):
    if isinstance(trusted_reviewers, str) or isinstance(caption_authors, str):
        raise ValueError("Reviewer and author identities must be explicit collections")
    reviewers, authors = set(trusted_reviewers), set(caption_authors)
    if not reviewers or not authors or any(not isinstance(name, str) or not name.strip()
                                           for name in reviewers | authors):
        raise ValueError("Named trusted reviewers and known caption authors are required")
    captions = read_json(Path(captions_path).read_bytes())
    raw_review = Path(approvals_path).read_bytes()
    review = read_json(raw_review)
    if not isinstance(captions, list) or not captions or not isinstance(review, dict):
        raise ValueError("Caption set and human review record are required")
    reviewer = review.get("reviewer_identity")
    if reviewer not in reviewers or reviewer in authors:
        raise ValueError("Caption review requires a trusted independent reviewer")
    try:
        when = datetime.fromisoformat(review["reviewed_at"])
        if when.tzinfo is None or when > datetime.now(UTC):
            raise ValueError("Invalid time")
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Caption review needs a real past timestamp with time zone") from exc
    if review.get("method") != "human_original_image_and_source":
        raise ValueError("Caption review must inspect original images and source provenance")
    decisions = review.get("caption_reviews")
    if not isinstance(decisions, list) or len(decisions) != len(captions):
        raise ValueError("Every caption needs a separate independent decision")
    by_id = {}
    for decision in decisions:
        if not isinstance(decision, dict) or decision.get("evidence_id") in by_id:
            raise ValueError("Invalid or duplicate caption decision")
        by_id[decision.get("evidence_id")] = decision
    ids = [caption.get("evidence_id") for caption in captions]
    if len(set(ids)) != len(ids) or set(by_id) != set(ids):
        raise ValueError("Caption decision identities differ from the candidate set")
    sources = read_json((Path(chart_root) / "chart-sources.json").read_bytes())["sources"]
    source_map = {source["source_asset_id"]: source for source in sources}
    approved = []
    for caption in captions:
        validate_description(caption["description"])
        source = source_map.get(caption["source"]["source_asset_id"])
        identity_fields = ("source_asset_id", "image_sha256", "accession", "pdf_url", "pdf_sha256", "page")
        if source is None or any(caption["source"].get(key) != source.get(key) for key in identity_fields):
            raise ValueError("Caption source differs from the unchanged original source manifest")
        meta = caption.get("metadata", {})
        if (caption.get("status") != "candidate" or meta.get("generated") is not True
                or meta.get("accession") != source["accession"]
                or meta.get("image_sha256") != source["image_sha256"]
                or hashlib.sha256(caption["content"].encode()).hexdigest() != meta.get("content_sha256")):
            raise ValueError("Caption content or source metadata changed")
        asset = Path(chart_root) / source["asset"]
        if (asset.is_symlink() or not asset.resolve().is_relative_to(Path(chart_root).resolve())
                or hashlib.sha256(asset.read_bytes()).hexdigest() != source["image_sha256"]):
            raise ValueError("Original caption image is missing or changed")
        decision = by_id[caption["evidence_id"]]
        basis = decision.get("basis") or decision.get("reviewer_notes")
        if (decision.get("caption_sha256") != caption_fingerprint(caption)
                or decision.get("image_sha256") != source["image_sha256"]
                or decision.get("decision") != "passed"
                or decision.get("original_image_checked") is not True
                or decision.get("source_provenance_checked") is not True
                or not isinstance(basis, str) or not basis.strip()):
            raise ValueError("Missing, stale or rejected independent caption approval")
        item = copy.deepcopy(caption)
        item.update(status="approved", review={"reviewer_identity": reviewer,
                    "reviewed_at": review["reviewed_at"], "basis": basis,
                    "approval_sha256": hashlib.sha256(raw_review).hexdigest()})
        item["source_at_generation"] = copy.deepcopy(caption["source"])
        item["source"] = copy.deepcopy(source)
        item["metadata"].update(independent_review="passed", ticker=source["ticker"],
                                 company=source["company"], source_locator=source["source_locator"])
        item["candidate_sha256"] = caption_fingerprint(caption)
        item["content"] = "Generated chart description; independently reviewed. " + json.dumps(item["description"], ensure_ascii=False)
        item["metadata"]["content_sha256"] = hashlib.sha256(item["content"].encode()).hexdigest()
        approved.append(item)
    return approved
