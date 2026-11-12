"""Extract six pinned original chart assets without claiming wider parser/index readiness.

Pass --source-dir for existing PDFs (the user's canonical course folder locally).
Network acquisition is optional and explicit. Verification never downloads files.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pypdf import PdfReader  # noqa: E402

SPECS = [
    ("AAPL", "0000320193-21-000105", 22, {"method": "embedded_image", "name": "Im197.jpg"}, "Comparison of 5-Year Cumulative Total Return", 1),
    ("NVDA", "0001045810-24-000029", 133, {"method": "render_crop", "bbox_top_left_points": [47, 163, 565, 485], "dpi": 144}, "Comparison of 5 Year Cumulative Total Return", 101),
    ("AMD", "0000002488-25-000012", 45, {"method": "embedded_image", "name": "X223.jpg"}, "Comparison of Cumulative Five Year Total Return", 1),
    ("INTC", "0000050863-25-000009", 52, {"method": "embedded_image", "name": "X204.jpg"}, "Comparison of Five-Year Cumulative Return", 1),
    ("CSCO", "0000858877-24-000017", 50, {"method": "render_crop", "bbox_top_left_points": [40, 175, 560, 455], "dpi": 144}, "Comparison of 5-Year Cumulative Total Return", 19),
    ("ADBE", "0000796343-25-000004", 101, {"method": "render_crop", "bbox_top_left_points": [55, 265, 565, 565], "dpi": 144}, "Comparison of Five-Year Cumulative Total Return", 1),
]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def extract(pdf_path, page, spec, scratch):
    if spec["method"] == "embedded_image":
        images = PdfReader(pdf_path).pages[page - 1].images
        matches = [im for im in images if im.name == spec["name"]]
        if len(matches) != 1:
            raise ValueError("Original embedded chart resource did not resolve uniquely.")
        return matches[0].data, ".jpg", None
    x0, y0, x1, y1 = spec["bbox_top_left_points"]
    scale = spec["dpi"] / 72
    # Render/crop directly from the source PDF; no image resampling/reconstruction.
    cache = scratch / "font-cache"
    cache.mkdir()
    config = scratch / "fonts.conf"
    config.write_text(f'<fontconfig><dir>/System/Library/Fonts</dir><dir>/Library/Fonts</dir><dir>/usr/share/fonts</dir><cachedir>{cache}</cachedir></fontconfig>')
    prefix = scratch / "chart"
    command = ["pdftoppm", "-f", str(page), "-l", str(page), "-singlefile", "-r", str(spec["dpi"]),
               "-x", str(round(x0 * scale)), "-y", str(round(y0 * scale)),
               "-W", str(round((x1 - x0) * scale)), "-H", str(round((y1 - y0) * scale)),
               "-png", str(pdf_path), str(prefix)]
    subprocess.run(command, check=True, capture_output=True,
                   env={**os.environ, "FONTCONFIG_FILE": str(config)})
    version = subprocess.run(["pdftoppm", "-v"], capture_output=True, text=True, check=True)
    return prefix.with_suffix(".png").read_bytes(), ".png", (version.stdout + version.stderr).splitlines()[0]


def prepare(source_dir, *, download=False):
    inventory = ROOT / "data/application_filings.json"
    rows = {r["accession"]: r for r in json.loads(inventory.read_text())}
    assets = ROOT / "data/charts/assets"
    assets.mkdir(exist_ok=True)
    sources = []
    for ticker, accession, page, spec, title, cover in SPECS:
        r = rows[accession]
        path = ROOT / "data/source/aapl-2021-rendition.pdf" if ticker == "AAPL" else source_dir / f"{ticker}_{accession}.pdf"
        if not path.exists() and download:
            import requests
            response = requests.get(r["rendition_url"], timeout=90,
                                    headers={"User-Agent": "FinRAG academic filing research"})
            response.raise_for_status()
            raw = response.content
            if sha(raw) != r["rendition_sha256"]:
                raise ValueError("Downloaded filing hash mismatch.")
            source_dir.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        if sha(path.read_bytes()) != r["rendition_sha256"]:
            raise ValueError("Pinned filing checksum mismatch.")
        with tempfile.TemporaryDirectory() as temp:
            raw, suffix, renderer = extract(path, page, spec, Path(temp))
        digest = sha(raw)
        name = digest + suffix
        destination = assets / name
        if destination.exists() and destination.read_bytes() != raw:
            raise ValueError("Immutable image destination differs.")
        destination.write_bytes(raw)
        locator = (f"PDF page {page}; embedded image {spec['name']}" if spec["method"] == "embedded_image"
                   else f"PDF page {page}; top-left point rectangle {spec['bbox_top_left_points']}")
        source = {"source_asset_id": f"{accession}:chart:{digest}", "image_sha256": digest,
                  "asset": f"assets/{name}", "company": r["issuer"], "ticker": ticker,
                  "accession": accession, "fiscal_period_end": r["period_end"], "title": title,
                  "page": page, "source_locator": locator, "pdf_url": r["rendition_url"],
                  "pdf_sha256": r["rendition_sha256"], "sec_source_url": r["source_url"],
                  "original_image_group": digest, "extraction": spec, "renderer": renderer,
                  "source_kind": "original_embedded_pdf_image" if spec["method"] == "embedded_image" else "original_pdf_chart_region_render",
                  "author_visual_check": "Original page and extracted graph checked; neighboring numerical table excluded.",
                  "independent_review": "pending", "filing_has_canonical_narrative_table_package": False, "chart_description_indexed": False,
                  "filing_identity_note": f"Pinned inventory rendition; Form 10-K cover at PDF page {cover}. Chart-inclusion/independent audit pending.",
                  "section_note": "Annual-report stock-performance graph. Regulatory non-filed-material notices are preserved in the linked original PDF; no legal filing-status claim for the graph."}
        if ticker == "AAPL":
            source["html_selector"] = "img[src='aapl-20210925_g2.jpg']"
            source["filing_has_canonical_narrative_table_package"] = True
        sources.append(source)
    manifest = {"schema_version": 1, "inventory_sha256": sha(inventory.read_bytes()), "sources": sources,
                "purpose": "Candidate chart-question/caption sources only; not wider narrative/table/index acceptance.",
                "duplicate_policy": "One image per issuer; alternate crops/renditions and same-image questions stay together. Apple only dev; other issuers only heldout.",
                "independent_review": "pending"}
    (ROOT / "data/charts/chart-sources.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args()
    result = prepare(args.source_dir, download=args.download)
    print(json.dumps({"sources": len(result["sources"]), "tickers": [s["ticker"] for s in result["sources"]]}, indent=2))
