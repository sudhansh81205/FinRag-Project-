"""One-command offline parse of the pinned Apple 2021 source snapshot."""

import argparse
import gzip
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.ingestion.filing_parser import ParseError, parse_filing, sha256  # noqa: E402


def write_atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        temp = Path(handle.name)
        handle.write(data)
    try:
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def run(manifest_path, output, *, chunk_size=1000, overlap=200):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    raw_path = ROOT / manifest["raw_path"]
    if raw_path.exists():
        raw = raw_path.read_bytes()
    else:
        archive = ROOT / manifest["source_archive"]
        compressed = archive.read_bytes()
        if sha256(compressed) != manifest["source_archive_sha256"]:
            raise ParseError("Source archive checksum mismatch.")
        raw = gzip.decompress(compressed)
    # Parse/validate all inputs before changing any existing outputs or manifest.
    narrative, tables, summary = parse_filing(raw, manifest, chunk_size=chunk_size, overlap=overlap)
    payloads = {
        "narrative.jsonl": "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in narrative).encode("utf-8"),
        "tables.jsonl": "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in tables).encode("utf-8"),
    }
    summary["output_sha256"] = {name: sha256(data) for name, data in payloads.items()}
    payloads["parsing_summary.json"] = json_bytes(summary)
    if not raw_path.exists():
        write_atomic(raw_path, raw)
    for name, data in payloads.items():
        write_atomic(output / name, data)
    manifest.update({
        "state": "parsed_not_indexed", "parser_version": summary["parser_version"],
        "raw_sha256": summary["source_sha256"], "parsed_record_count": summary["total_records"],
        "next_step": "Follow docs/plan/schedule.json: Likhit cells/PDF/chart sources (Nov 4), Shanay independent validation (Nov 5), then Likhit BGE/exact FAISS (Nov 6) only after the input gate passes. MiniLM/Chroma is historical.",
    })
    write_atomic(manifest_path, json_bytes(manifest))
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/filing_manifest.json")
    parser.add_argument("--output", type=Path, default=ROOT / "data/processed/apple-2021")
    parser.add_argument("--chunk-size", type=int, default=1000)
    parser.add_argument("--overlap", type=int, default=200)
    args = parser.parse_args()
    try:
        summary = run(args.manifest, args.output, chunk_size=args.chunk_size, overlap=args.overlap)
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"Parse failed: {exc}\n")
    print(json.dumps({"status": "parsed_not_indexed", "output": str(args.output),
                      "narrative_records": summary["narrative_records"],
                      "table_records": summary["table_records"],
                      "source_sha256": summary["source_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
