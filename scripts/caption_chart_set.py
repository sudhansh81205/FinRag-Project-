"""Caption original chart images with the frozen provider/prompt, never QA labels.

This is corpus preprocessing, not heldout answering or evaluation. Existing Apple
caption is reused; new raw drafts and explicit source annotations remain unreviewed.
"""

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.charts.caption import apply_author_corrections, caption_chart  # noqa: E402
from src.llm.client import UnifiedLLMClient  # noqa: E402


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def run(output):
    started = time.monotonic()
    chart_root = ROOT / "data/charts"
    manifest_path = chart_root / "chart-sources.json"
    manifest = json.loads(manifest_path.read_text())
    # Only source annotations/images are read; no question-set/answer file is loaded.
    annotations_path = chart_root / "source-author-annotations.json"
    annotations = json.loads(annotations_path.read_text())
    profile_path = ROOT / "configs/gemma3-4b.json"
    profile = json.loads(profile_path.read_text())
    client = UnifiedLLMClient.from_profile(profile)
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    raw_captions, candidates = [], []
    for source in manifest["sources"]:
        if source["ticker"] == "AAPL":
            old = json.loads((ROOT / "docs/reports/2026-11-09-rushil/final/chart-captions.json").read_text())[0]
            if old["metadata"]["image_sha256"] != source["image_sha256"]:
                raise ValueError("Existing development caption source changed.")
            candidates.append(old)
            continue
        clock = time.monotonic()
        caption = caption_chart(source, chart_root / source["asset"], client)
        caption["wall_seconds"] = round(time.monotonic() - clock, 3)
        raw_captions.append(caption)
        write(output / f"{source['ticker']}-raw-caption.json", caption)
        if caption["status"] == "candidate":
            caption = apply_author_corrections(caption, annotations[source["ticker"]], chart_root / source["asset"])
        candidates.append(caption)
        write(output / f"{source['ticker']}-candidate-caption.json", caption)
        print(source["ticker"], caption["status"], caption["wall_seconds"], flush=True)
    write(output / "candidate-captions.json", candidates)
    report = {"code_revision": revision, "scope": "Frozen-prompt original-image caption preprocessing only; no heldout QA, tuning, scoring or answer generation.",
              "profile_sha256": hashlib.sha256(profile_path.read_bytes()).hexdigest(),
              "source_manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
              "author_annotation_sha256": hashlib.sha256(annotations_path.read_bytes()).hexdigest(),
              "new_model_caption_count": len(raw_captions), "reused_dev_caption_count": 1,
              "candidate_count": len(candidates), "passed": all(c["status"] == "candidate" for c in candidates),
              "independent_review": "pending", "evaluation_ready": False,
              "wall_seconds": round(time.monotonic() - started, 3),
              "prompt_hashes": sorted({c['generation']['prompt_sha256'] for c in candidates if 'generation' in c}),
              "source_files_sha256": {n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in (
                  'scripts/caption_chart_set.py','src/charts/caption.py','src/llm/client.py','src/llm/ollama_profile.py')}}
    write(output / "caption-report.json", report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "output/chart-set-captions")
    args = parser.parse_args()
    report = run(args.output)
    print(json.dumps(report, indent=2))
    sys.exit(0 if report["passed"] else 1)
