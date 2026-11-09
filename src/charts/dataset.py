"""Candidate chart-set integrity, source resolution and split checks; no model calls."""

import hashlib
import json
from pathlib import Path

from .questions import audit_questions


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def local(root, relative):
    if not isinstance(relative, str):
        raise ValueError("A relative dataset path is required.")
    path = root / relative
    if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("Dataset path escapes its root.")
    return path


def load_candidate_set(directory):
    directory = Path(directory)
    index = json.loads((directory / "question-set.json").read_text())
    manifest_path = local(directory, index["source_manifest"])
    manifest = json.loads(manifest_path.read_text())
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
        cases.extend(json.loads(raw))
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
