"""Validate candidate chart labels and prevent original-image split leakage."""

import re


def audit_questions(cases):
    seen, groups, hashes, sources, counts = set(), {}, {}, {}, {"dev": 0, "heldout": 0}
    for case in cases:
        if not isinstance(case, dict) or not all(case.get(k) for k in (
            "id", "question", "answer", "image_sha256", "source_asset_id", "source_locator", "answer_basis")):
            raise ValueError("Incomplete source-linked chart question.")
        if case["id"] in seen:
            raise ValueError("Duplicate question identity.")
        seen.add(case["id"])
        digest, split = case["image_sha256"], case.get("split")
        if not re.fullmatch(r"[a-f0-9]{64}", digest) or split not in counts:
            raise ValueError("Invalid image identity or split.")
        # A supplied duplicate-group hash groups alternate crops/renditions too.
        group = case.get("original_image_group", digest)
        if not isinstance(group, str) or not group:
            raise ValueError("Missing original image group.")
        if (groups.get(group, split) != split or hashes.get(digest, split) != split
                or sources.get(case["source_asset_id"], split) != split):
            raise ValueError("Original or near-duplicate image crosses development/heldout split.")
        groups[group] = split
        hashes[digest] = split
        sources[case["source_asset_id"]] = split
        counts[split] += 1
        if case.get("independent_review") != "pending":
            raise ValueError("This builder accepts candidates only; independent labels require a separate audit.")
    shortfall = {"dev": max(0, 15 - counts["dev"]), "heldout": max(0, 35 - counts["heldout"])}
    return {"status": "candidate_scope_unmet" if any(shortfall.values()) else "candidate_target_met",
            "counts": counts, "distinct_original_images": len(groups), "target": {"dev": 15, "heldout": 35},
            "shortfall": shortfall, "independent_review": "pending",
            "evaluation_ready": False}
