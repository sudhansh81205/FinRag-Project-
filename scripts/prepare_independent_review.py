"""Prepare inspectable chart/caption decisions; every decision starts unreviewed.

R7/R11/R12. This packet contains no generated signature, human identity, approval
or completed-output audit. An eligible person must inspect the original sources.
"""

import argparse
import hashlib
import html
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.charts.dataset import case_fingerprint, load_candidate_set  # noqa: E402


def build_packet(output):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    charts = ROOT / "data/charts"
    cases, _, audit = load_candidate_set(charts)
    sources = json.loads((charts / "chart-sources.json").read_text())["sources"]
    by_asset = {s["source_asset_id"]: s for s in sources}
    captions_path = ROOT / "docs/reports/2026-11-09-chart-set/captions/candidate-captions.json"
    captions = json.loads(captions_path.read_text())
    template = {
        "reviewer_identity": None, "reviewed_at": None, "method": None,
        "instruction": "Only the actual eligible reviewer fills identity/time/method and each decision after inspecting its unchanged source; rejected/uncertain cases remain explicit.",
        "candidate_binding": audit,
        "cases": [{"id": c["id"], "case_sha256": case_fingerprint(c),
                   "decision": "unreviewed", "original_image_checked": False,
                   "source_provenance_checked": False, "reviewer_notes": ""} for c in cases],
        "caption_reviews": [{"evidence_id": c["evidence_id"],
                             "caption_sha256": hashlib.sha256(json.dumps(c, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
                             "image_sha256": c["metadata"]["image_sha256"],
                             "decision": "unreviewed", "original_image_checked": False,
                             "source_provenance_checked": False, "reviewer_notes": ""} for c in captions],
        "generated_output_audit": {"completed": 0, "required": 50,
                                   "note": "These are input reviews, not the independently audited generated outputs."},
    }
    (output / "review-marks-template.json").write_text(json.dumps(template, indent=2) + "\n")
    sections = []
    for source in sources:
        image = os.path.relpath(charts / source["asset"], output)
        associated = [c for c in cases if c["source_asset_id"] == source["source_asset_id"]]
        caption = next(c for c in captions if c["source"]["source_asset_id"] == source["source_asset_id"])
        rows = "".join(f"<tr><td>{html.escape(c['id'])}<br>{html.escape(c['split'])}</td><td>{html.escape(c['question'])}</td><td>{html.escape(str(c['answer']))}<br><small>{html.escape(c['answer_basis'])}</small></td></tr>" for c in associated)
        sections.append(f"<section><h2>{html.escape(source['ticker'])}</h2><p>{html.escape(source['source_asset_id'])}</p><a href='{html.escape(source['pdf_url'], quote=True)}'>Original PDF, page {source['page']}</a><p><img src='{html.escape(image, quote=True)}' alt='Original {html.escape(source['ticker'])} chart'></p><h3>Generated, author-corrected caption — independent review pending</h3><pre>{html.escape(json.dumps(caption['description'], indent=2))}</pre><table><thead><tr><th>ID / split</th><th>Question</th><th>Candidate answer and basis</th></tr></thead><tbody>{rows}</tbody></table></section>")
    page = "<!doctype html><html lang='en'><meta charset='utf-8'><title>FinRAG independent review packet</title><style>body{font:17px/1.6 system-ui;max-width:1100px;margin:40px auto;padding:0 20px;color:#171717}section{border-top:2px solid;margin-top:45px;padding-top:20px}img{max-width:100%;max-height:650px}table{border-collapse:collapse;width:100%}td,th{border:1px solid #bbb;padding:12px;text-align:left;vertical-align:top}pre{white-space:pre-wrap;background:#f4f4f4;padding:18px}small{color:#555}</style><h1>Independent input review — pending</h1><p>50 questions (15 development / 35 heldout), six original images and six captions. Inspect each original image and PDF locator. Record pass, reject or uncertainty in <a href='review-marks-template.json'>the blank decision file</a>. Do not infer point values from curve positions. A label author cannot independently approve their own work.</p><p>This packet neither authenticates a human reviewer nor completes the separate 50-generated-output audit. Final experiment gates remain closed until real acceptance and the required runtime/data bindings exist.</p>" + "".join(sections) + "</html>"
    (output / "index.html").write_text(page)
    return {"questions": len(cases), "original_images": len(by_asset), "captions": len(captions),
            "all_decisions": "unreviewed", "output": str(output)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "output/nov17/independent-review")
    print(json.dumps(build_packet(parser.parse_args().output), indent=2))
