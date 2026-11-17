"""Publish inspectable original chart candidates, never accepted financial evidence.

R6/R11 common G input inspection. Only hash-verified original bytes are copied;
this creates no review decisions and does not enable the chart answer route.
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.charts.approval import caption_fingerprint  # noqa: E402
from src.charts.dataset import case_fingerprint, load_candidate_set  # noqa: E402


def build(root=ROOT):
    root = Path(root)
    chart_root = root / "data/charts"
    cases, _, audit = load_candidate_set(chart_root)
    sources = json.loads((chart_root / "chart-sources.json").read_text())["sources"]
    captions = json.loads((root / "docs/reports/2026-11-09-chart-set/captions/candidate-captions.json").read_text())
    destination = root / "web/public/review"
    destination.mkdir(parents=True, exist_ok=True)
    records = []
    for source in sources:
        candidate = chart_root / source["asset"]
        asset = candidate.resolve()
        if not asset.is_relative_to(chart_root.resolve()) or candidate.is_symlink():
            raise ValueError("Chart asset escapes its source directory")
        if hashlib.sha256(asset.read_bytes()).hexdigest() != source["image_sha256"]:
            raise ValueError("Original chart bytes changed")
        caption = next(c for c in captions if c["source"]["source_asset_id"] == source["source_asset_id"])
        if caption["metadata"]["image_sha256"] != source["image_sha256"]:
            raise ValueError("Caption refers to a different original image")
        name = source["image_sha256"] + asset.suffix.lower()
        shutil.copyfile(asset, destination / name)
        records.append({"source_asset_id": source["source_asset_id"], "ticker": source["ticker"],
                        "image": "/review/" + name, "image_sha256": source["image_sha256"],
                        "source_url": source["pdf_url"], "page": source["page"],
                        "description": caption["description"], "status": "independent_review_pending",
                        "questions": [{key: case[key] for key in ("id", "split", "question", "answer", "answer_basis")}
                                      for case in cases if case["source_asset_id"] == source["source_asset_id"]]})
    result = {"status": "candidate_only", "answering_enabled": False,
              "note": "Original input review only; no human approval or final answer is implied.",
              "audit": audit, "charts": records}
    (destination / "charts.json").write_text(json.dumps(result, indent=2) + "\n")
    template = {
        "reviewer_identity": None, "reviewed_at": None, "method": None,
        "instruction": "Only the eligible independent human fills identity/time/method and decisions after inspecting original sources. This blank file is not approval.",
        "candidate_binding": audit,
        "cases": [{"id": case["id"], "case_sha256": case_fingerprint(case),
                   "decision": "unreviewed", "original_image_checked": False,
                   "source_provenance_checked": False, "reviewer_notes": ""} for case in cases],
        "caption_reviews": [{"evidence_id": item["evidence_id"], "caption_sha256": caption_fingerprint(item),
                             "image_sha256": item["metadata"]["image_sha256"], "decision": "unreviewed",
                             "original_image_checked": False, "source_provenance_checked": False,
                             "reviewer_notes": ""} for item in captions],
        "generated_output_audit": {"completed": 0, "required": 50,
                                   "note": "Separate generated-output review is not supplied by this input template."}}
    (destination / "review-marks-template.json").write_text(json.dumps(template, indent=2) + "\n")
    return {"charts": len(records), "questions": len(cases), "answering_enabled": False}


if __name__ == "__main__":
    print(json.dumps(build()))
